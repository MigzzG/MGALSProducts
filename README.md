# Parametric Gutter DXF Web Application

This Streamlit application provides a browser form for the parametric
Trimline gutter DXF generator.

## What it does

The user enters the main profile, roof geometry, machining and stop-end
values. The application then:

- calculates F from the perpendicular gutter arm depth;
- calculates BC and FG from the roof pitch;
- calculates the girth and small-end dimensions;
- validates the profile;
- displays a section preview;
- generates the complete DXF;
- provides a DXF download button.

## Files

- `app.py` — browser interface.
- `trimline_engine.py` — calculations and DXF-generation wrapper.
- `trimline_generator_template.py` — the full approved DXF algorithm.
- `requirements.txt` — required Python packages.
- `run_app.bat` — Windows launcher after Python has been installed.

Do not rename or remove the generator template.

## Run on a Windows PC

Open Command Prompt in this folder and run:

```bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit normally opens the application in the default browser.

## Run on a company server

IT can install the requirements and run:

```bat
python -m streamlit run app.py --server.address 0.0.0.0
```

Colleagues on the same network can then use the server address supplied
by IT.

## Deploy as a hosted web application

The folder can be uploaded to a private Git repository and deployed using
an approved Python/Streamlit hosting service. Company approval should be
obtained before uploading technical drawings or source code outside the
company network.

## User workflow

1. Open the web page.
2. Enter A, B, C, D, E, G and H.
3. Enter roof pitch and gutter arm depth.
4. Review the calculated F, girth, BC and FG.
5. Adjust the advanced manufacturing or stop-end values when required.
6. Press **Generate DXF**.
7. Press **Download generated DXF**.
8. Open and check the DXF in the approved CAD/CAM software.

## Important

The `New Up Mark` block name and its internal hierarchy are retained by
the generator because the punching-machine macro relies on that exact
block name.
