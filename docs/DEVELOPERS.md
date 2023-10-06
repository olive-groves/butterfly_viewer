# Developers

## Contributing to `butterfly_viewer`

You can contribute to `butterfly_viewer` with a pull request by following these steps:

1. Fork the [repo<sup>↗</sup>](https://github.com/olive-groves/butterfly_viewer).
2. Create a branch: `git checkout -b <branch_name>`.
3. Make your changes and commit them: `git commit -m '<commit_message>'`
4. Push to the original branch: `git push origin <project_name>/<location>`
5. Create the pull request.

Or see the GitHub documentation on [creating a pull request<sup>↗</sup>](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request).

## Creating the executable and setup installer

The installer executable for Butterfly Viewer is created by first bundling the app with PyInstaller and then creating a setup installer with Inno Setup.

### Install PyInstaller

PyInstaller must be installed with the same packages as the environment of the Butterfly Viewer to bundle a functioning dist and executable.

With ```conda``` you can do this by cloning the environment you use for Viewer, activating that clone, and then installing PyInstaller. 

#### Cloning from `env` subfolder

If you use an `env` subfolder in the root of `butterfly_viewer` for your Viewer environment, first open Anaconda Prompt and change the directory to the root directory.

```
cd C:\path\to\the\butterfly_viewer\
```

Clone the environment into a new subfolder named `env_installer`, using the full directory of `env` in the command.

```
conda create --prefix ./env_installer --clone C:\path\to\the\butterfly_viewer\env
```

Activate the environment.

```
conda activate ./env_installer
```

#### Cloning from `environment.yml`

You can also create and activate a clone of the environment directly from the ```environment.yml``` in the root directory of ```butterfly_viewer```:

into a subfolder;
```
conda env create --file environment.yml --prefix ./env_installer
conda activate ./env_installer
```

or in a new named environment.
```
conda env create --file environment.yml --name viewer_installer
conda activate viewer_installer
```

#### Install

With the installer environment activated, install PyInstaller:
```
conda install pyinstaller
```

### Run PyInstaller to bundle Butterfly Viewer

Run PyInstaller with the following command while in the **source code** directory ```\butterfly_viewer\butterfly_viewer```.

```
cd butterfly_viewer
pyinstaller --onedir --windowed --icon=icons\icon.ico butterfly_viewer.py
```

> PyInstaller not working? Make sure you've changed directory to the source code directory (the subfolder `butterfly_viewer` within the repo itself).

The executable runs fastest when not bundled into one file (otherwise it needs to unpack all packages on each startup), so we enforce the default ```--onedir```. We also enforce ```--windowed``` to prevent the console window from opening when the executable runs. We add the app icon with the ```--icon``` argument.

### Use Inno Setup to create a setup installer

Steps to use Inno Setup are not yet documented.

## Generating documentation with pdoc

The docs branch is exclusively for generating documentation with pdoc.

In other words, it is a one-way street to docs: only pull main into docs; never pull docs into main.

> Note: We use [pdoc](https://pdoc.dev/), *not* pdoc3.

### 0. Pull main into docs

Bring the latest code into the docs branch with a pull request main>docs.

### 1. Checkout docs branch

Checkout the docs branch.

### 2. Open conda and change directory to the root folder of butterfly_viewer

```
cd C:\butterfly_viewer
```

### 3. (If not yet done) Install docs environment

Install the docs environment with conda using environment_docs.yml, which is a modified version of the Butterfly Viewer's base environment with pdoc and Python 3.7 (which is required for pdoc). This .yml is available in the docs branch. :

```
conda env create -f environment_docs.yml --prefix ./env_docs
```

### 4. Add `"Returns"` to pdoc Google docstring sections

pdoc does not include **Returns** in its list of section headers for Google's docstring style guide. This means the returns are not styled like those under **Arguments**. 

To give that styling to returns, do this:
1. Locate `docstrings.py` in the pdoc site package which installed with the docs environment, likely here:

```
...\env_docs\Lib\site-packages\pdoc\docstrings.py
```

2. Add `"Returns"` to the list variable `GOOGLE_LIST_SECTIONS`, which is around line 80 or so.

```
GOOGLE_LIST_SECTIONS = ["Args", "Raises", "Attributes", "Returns"]
```

3. Save `docstrings.py`

### 5. Activate docs environment 

```
conda activate ./env_docs
```

### 6. Add to path the butterfly_viewer source folder

```
set PYTHONPATH=C:\butterfly_viewer\butterfly_viewer
```

### 7. Change directory to source folder

```
cd butterfly_viewer
```

### 8. Run pdoc

Run pdoc with the following command while in the source code directory ```\butterfly_viewer\butterfly_viewer```:

```
pdoc C:\butterfly_viewer\butterfly_viewer -t C:\butterfly_viewer\docs\_templates --docformat google --logo https://olive-groves.github.io/butterfly_viewer/images/viewer_logo.png --logo-link https://olive-groves.github.io/butterfly_viewer/ --favicon https://olive-groves.github.io/butterfly_viewer/images/viewer_logo.png -o C:\butterfly_viewer\docs\
```

> You will need to edit the full directory of the repo in the above pdoc command (`C:\butterfly_viewer\...`) to match that on your machine.

We call the custom templates folder with ```-t```. We enforce the google docstring format with ```--docformat```. We add the webpage logo and favicon with ```--logo``` and ```--favicon```. We export the docs to the docs subfolder with ```-o```.

### 9. Commit and push

Commit and push the updated docs to the docs branch.

### 10. Un-checkout docs branch

Continue development only after having un-checked out of the docs branch.

### Multi-line commands

You can re-run pdoc by copying and pasting the following lines together (steps 2 and 5–8), making sure to replace the absolute paths with those of the repo on your own machine:

```
cd C:\butterfly_viewer
conda activate ./env_docs
cd butterfly_viewer
set PYTHONPATH=.
pdoc C:\butterfly_viewer\butterfly_viewer -t ../docs/_templates --docformat google --logo https://olive-groves.github.io/butterfly_viewer/images/viewer_logo.png --logo-link https://olive-groves.github.io/butterfly_viewer/ --favicon https://olive-groves.github.io/butterfly_viewer/images/viewer_logo.png -o ../docs
```

# Credits

Butterfly Viewer is by Lars Maxfield.

Butterfly Viewer uses elements of [@tpgit<sup>↗</sup>](https://github.com/tpgit)'s *PyQt MDI Image Viewer* (with changes made), which is made available under the Creative Commons Attribution 3.0 license.


# License
<!--- If you're not sure which open license to use see https://choosealicense.com/--->

Butterfly Viewer is made available under the [GNU GPL v3.0<sup>↗</sup>](https://www.gnu.org/licenses/gpl-3.0.en.html) license or later. For the full-text, see the `LICENSE.txt` file in the root directory of the Viewer's GitHub [repo<sup>↗</sup>](https://github.com/olive-groves/butterfly_viewer).