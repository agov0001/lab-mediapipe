# Mediapipe

We try out mediapipe library. 

## Getting Started
You need to re-create the virtual environment once and the activate it each time you want to play.

To recreate it cd to project root then enter:
```
> python -m venv .venv
> .venv\Scripts\activate or source .venv/bin/activate
> pip install -r setup/requirements.txt
```

Make sure you have the lab-data checked out under `../data` or `./var` folder relative project root.

Now you can run and experiment with various cases by running:
```
> python src/run_mpvision.py [case i.e. faces]
``` 

Oh yes this project uses files from [lab-data](https://github.com/agov0001/lab-data) repo so check it out side by side.