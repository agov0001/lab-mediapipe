"""
environment information and configuration.
"""
import os,sys
import logging as log
import json
import time


log_debug=log.debug
log_info=log.info
log_error=log.error
log_warn=log.warn
log_critical=log.critical

basedir = os.getenv('APP_BASEDIR') or os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
workdirs=(
    os.getenv('APP_WORKDIR',os.getcwd()+"/var").replace("\\","/").replace("/./","/").rstrip("/")+"/",
    (os.getcwd()+"/../data").replace("\\","/").replace("/./","/").rstrip("/")+"/",
    (os.getcwd()+"/../lab-data").replace("\\","/").replace("/./","/").rstrip("/")+"/"
)
confdir = os.getenv('APP_CONFDIR') or os.getcwd()+"/etc"
basedir=basedir.replace("\\","/").replace("/./","/").rstrip("/")+"/"
confdir=confdir.replace("\\","/").replace("/./","/").rstrip("/")+"/"
def get_basepath(rel_path):
    return basedir+rel_path.lstrip("/").replace("\\","/").replace("//","/").replace("/./","/")
def get_workpath(rel_path):
    rel_path=rel_path.lstrip("/").replace("\\","/").replace("//","/").replace("/./","/")
    for workdir in workdirs:
        abs_path=workdir+rel_path
        if os.path.exists(abs_path):
            return abs_path
    return None

def get_confpath(rel_path):
    return confdir+rel_path.lstrip("/").replace("\\","/").replace("//","/").replace("/./","/")

APP_STATE="~app.state"
APP_ENABLED="app.enabled" # enabled modules
LOG_LEVEL="log.level"
LOG_DIR="LOG.DIR"
CODE_DIR="CODE.DIR"
DATA_DIR="DATA.DIR"
DATA_DIR="DATA.DIR"
SEARCHPATHS="SEARCH.PATHS"

config={
}


def estr(ex,hdr=True,typ=True,trace=3,indent="    ",inline=False):
    """ stringifies exception to provide nice printed message """
    lns=[]
    sval=""
    if not inline:
        inline=(not hdr and typ and trace==1)
    else:
        (hdr,typ,trace,indent)=(False,True,1 if trace else 0,"")
    if hdr:
        sval=str(ex)
        lns.append(sval)
    if isinstance(ex,Exception):
        if hasattr(ex,"response"):
            det=None
            det_prefix="detail:" if not inline else ""
            resp=getattr(ex,"response")
            if resp is not None:
                det=resp.text
                if det and det.startswith("{"):
                    payload=json.loads(det)
                    det=payload.get("message",payload.get("detail",None))
                elif resp.headers.get('Content-Type',"")=="text/plain":
                    pass
                else:
                    det=None
            if det:
                typ=False if inline else True
                lns.append("%s %s%s"%(indent,det_prefix,det))
        if typ:
            tmsg=repr(ex).replace(sval,"").replace(",)",")").replace("('')","").replace("(\"\")","")
            typ_prefix="type:" if not inline else ""
            lns.append("%s %s%s"%(indent,typ_prefix,tmsg))
        if trace>0:
            import traceback
            (typ,_val,tb)=sys.exc_info()
            se=traceback.extract_tb(tb)
            for (file,line,fn,txt) in reversed(se):
                if trace<=0:
                    break
                trace=trace-1
                file=file.replace("\\","/")
                rindex=file.rfind("/")
                rindex=file.rfind("/",0,max(0,rindex))
                rfile=file[rindex+1:]
                lns.append("%s at %s(%s:%r):\t%s"%(indent,fn,rfile,line,txt))
    delim="" if inline else "\n"
    return delim.join(lns)
def log_init(level=log.DEBUG):
    """initialize logging - return name of file."""
    class PckgFilter:
        """ we augment log records with package field."""
        def filter(self, record):
            p=record.pathname.replace("\\","/").replace(record.filename,"")
            index=p.rfind("/",0,-1)
            p=p[index+1:-1]
            record.package=p
            return True
    if isinstance(level,str):
        level=level.lower()
        opts={"debug":log.DEBUG,"info":log.INFO,"warn":log.WARN,"warning":log.WARN,"error":log.ERROR,"fatal":log.FATAL}
        level=opts.get(level,log.WARN)
    logFormatter = log.Formatter(
        fmt='%(asctime)s -%(levelname)7s: %(package)s.%(module)s:%(lineno)s \t- %(message)s',
        datefmt='%H:%M:%S'
        )
    rootLogger = log.getLogger()
    myfilter=PckgFilter()
    rootLogger.addFilter(myfilter)
    rootLogger.handlers=[]
    if level:
        rootLogger.setLevel(level)
        consoleHandler = log.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        consoleHandler.addFilter(myfilter)
        consoleHandler.setLevel(level)
        rootLogger.addHandler(consoleHandler)
    else:
        rootLogger.setLevel(log.ERROR)
        return None
    logFile=None
    wdir=config.get(LOG_DIR)
    if wdir:
        logFile=time.strftime('%Y-%m-%d')+".log"
        logFile=os.path.join(wdir,logFile)
        if not os.path.exists(os.path.dirname(logFile)):
            try:
                os.makedirs(os.path.dirname(logFile))
            except OSError as exc: # Guard against race condition
                import errno
                if exc.errno != errno.EEXIST:
                    raise
        fileHandler = log.FileHandler(logFile)
        fileHandler.setFormatter(logFormatter)
        fileHandler.addFilter(myfilter)
        fileHandler.setLevel(level or log.ERROR)
        rootLogger.addHandler(fileHandler)
    return logFile
def log_level(level=log.ERROR):
    """ change log level.

    calling this method with default argument sets log.ERROR level which will supress warnings.
    this is often useful in dask workers to avoid verbose output.
    """
    rootLogger = log.getLogger()
    old=rootLogger.getEffectiveLevel()
    rootLogger.setLevel(level)
    for key in log.Logger.manager.loggerDict:
        l=log.getLogger(key)
        l.setLevel(level)
    dl=log.getLogger("distributed.utils_perf")
    if dl:
        dl.setLevel(level)
    config[LOG_LEVEL]=level
    return old

def init(stor=None):
    """ initialize environment.

    If called this method checks READY flag and skips if True.
    Otherwise it parses console arguments and updates various properties such as
    FIRST_DATE,LAST_DATE,INTERVAL, DOI etc.
    It also initializes logging.
    storage_initi is called but the way it works is it will not initialize values already set.
    """
    global config
    is_ready=config.get(APP_STATE) is not None
    if is_ready:
        return 0
    try:
        if stor:
            config=stor
        log_init(config.get(LOG_LEVEL,log.WARN))
        ts=time.strftime('%Y-%m-%d %H:%M:%S')
        log_info("starting new session on:{}".format(ts))
        config[APP_STATE]="ready"
        return 1
    except ValueError as e:
        log_error(estr(e))
        return -1