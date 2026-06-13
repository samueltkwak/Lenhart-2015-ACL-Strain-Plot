# ACL Model Visualization

Interactive Dash visualization of ACL strain for the Lenhart 2015 model workflow.

## Current Model Status

The app does not load strain data from a repository, database, or external service. `app.py` evaluates the embedded 6DOF equations for the ACLam and ACLpl bundles and individual fibers.

The deployed UI is 6DOF-only and evaluates the embedded 6DOF equations for ACLam/ACLpl bundle strain and individual fiber strain.

## Usage

- Use the flexion slider to control knee flexion in 1 degree increments.
- Drag the adduction/internal-rotation pad dot to set those angles in 1 degree increments.
- Drag the translation pad dot to set anterior/posterior and medial/lateral tibial translation.
- Use the vertical slider to set proximal/distal translation.
- Inspect the anatomy panel to see the right femur, tibia, fibula, and ACL fibers respond to the selected kinematics.
- Hover over the fiber strain panel to read individual fiber strain, reference length, and current length.
- Rotate and zoom the strain surfaces and anatomy model directly in their plots.

## Local Setup

```bash
pip install -r requirements.txt
python app.py
```

## Render Deployment

This repository includes both a `Procfile` and `render.yaml`.

Render can start the Dash app with:

```bash
gunicorn app:server
```

For a manual Render web service setup:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:server`
- Runtime: Python
