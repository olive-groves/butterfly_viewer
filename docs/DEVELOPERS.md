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

## Updating packages in `environment.yml` 

If you change the environment in order to an fix issue, add a feature, or simply reduce a dependency, you can update the packages in the `environment.yml` of the root by exporting the new environment while it is activated and then replacing that existing YML in the root:

```
conda activate NAME_OF_ENV

conda install/remove PACKAGE_1
conda install/remove PACKAGE_2
...
conda install/remove PACKAGE_N

conda env export > environment.yml
```

> Take care to update both `environment.yml` and `environment_docs.yml` in the branch `docs`. If unable to do so, please create a GitHub issue requesting it be updated. 


# Credits

Butterfly Viewer is by Lars Maxfield.

Butterfly Viewer uses elements of [@tpgit<sup>↗</sup>](https://github.com/tpgit)'s *PyQt MDI Image Viewer* (with changes made), which is made available under the Creative Commons Attribution 3.0 license.


## Techniques and inspiration

Butterfly Viewer uses well-known image comparison techniques found in both commercial and free software, some of which helped inspire the Viewer itself.


### Sliders and overlays

A sliding overlay is simply a before-and-after image slider in two-dimensions where the top-left image persists while the other three images are layed over it, hence the name "sliding overlay". 

The underlying slider functionality is a commonly used method for comparing images as well as maps, videos, and other spatial information.

#### Adobe Lightroom
['Before and After' mode (video)](https://www.youtube.com/watch?v=sBP2Xe21t18&t=101s) (David Mark Erickson, 2016) and described in this [blog post](https://www.tipsquirrel.com/comparing-before-and-after-views-in-lightroom/) (Ashu Mittal, 2009) 

#### OpenSeadragon
[Programmable slider (demo)](https://codepen.io/imoskvin/pen/yOXqvO) (Illya Moskvin, 2016 & 2021) 

#### IIPMooViewer 2.0
['Multi-model overlays' (demo)](https://merovingio.c2rmf.cnrs.fr/iipimage/iipmooviewer/vangogh.html) (2011) with [other demos](https://iipimage.sourceforge.io/demo) 

#### Georeferencer
[Mouse-follow 'Swipe' mode (demo)](https://uu.oldmapsonline.org/compare#map/631781111740) and described in this [documentation](https://www.davidrumsey.com/view/georeferencer) (2017) 

#### Leaflet.Sync plugin for Leaflet
['Offset' mode (demo)](https://jieter.github.io/Leaflet.Sync/examples/multiple_offset.html) with [animation](https://raw.githubusercontent.com/jieter/Leaflet.Sync/HEAD/offset_animation.gif) and available in its [GitHub repo](https://github.com/jieter/Leaflet.Sync) (2013) 

#### The New York Times
[Visual technique (video)](https://www.instagram.com/reel/C30XT07O5UK/) (Steven Kurutz et al., 2024) 

#### Affinity Designer
['Split-Screen View' mode (video)](https://design.tutsplus.com/courses/affinity-designer-quick-start/lessons/split-screen-view-with-slider) (Kezz Bracey, 2017) 

#### 3DVista
['Dual Viewer' tool (video)](https://youtu.be/udQHKP1Da-I?si=8_Xz2ofyiB-NEHiG&t=9) 

#### MapBrowser
['Comparison' tool (video)](https://www.youtube.com/watch?v=pcmfn5fjPXw&t=97s) 

#### 'Swipe' in ArcGIS and related apps
['Swipe' tool (documentation)](https://www.esri.com/news/arcuser/0705/91faster.html) (2005) 

[Compilation (blog post)](https://www.esri.com/arcgis-blog/products/arcgis-online/mapping/swipe-compare-apps/#landsat) with numerous screenshots and links (Bern Szukalski, 2021–2023): 
- ArcGIS Instant Apps (Media Map, Imagery Viewer, Atlas, Portfolio, Exhibit, Compare)
- App builders (Experience Builder, Web AppBuilder)
- Imagery apps (World Imagery Wayback, Sentinel-2 Land Cover Explorer, Landsat Explorer, Sentinel Explorer)
- ArcGIS StoryMaps


### Synchronized panning and zooming

#### Adobe Lightroom
['Before and After' mode](#adobe-lightroom) 

#### OpenSeadragon
[Programmable syncing (demo)](https://codepen.io/iangilman/pen/BpwBJe) (Ian Gilman, 2017) 

#### FastStone Image Viewer
['Compare' window (blog)](https://www.imagingtips.com/faststone/controlbar/compare/0compare.shtml) (Joe Holler, 2009) 

#### Georeferencer
['Grid' mode (demo)](https://davidrumsey.oldmapsonline.org/compare#686492204670) 

Described in this [documentation](https://www.davidrumsey.com/view/georeferencer) (2017) 

#### Leaflet.Sync plugin for Leaflet
['Dual' mode (demo)](https://jieter.github.io/Leaflet.Sync/examples/dual.html) (2013) 

[GitHub repo](https://github.com/jieter/Leaflet.Sync) 

#### IIPMooViewer 2.0
['Dual synchronized streamed viewing' (demo)](https://merovingio.c2rmf.cnrs.fr/iipimage/iipmooviewer-2.0/synchro.html) (2011) 

[Other demos](https://iipimage.sourceforge.io/demo) 

#### GeTeach.com
[Default design (demo)](https://geteach.com/) 

#### BreezeBrowser Pro
['Compare images' window (documentation)](https://www.breezesys.com/BreezeBrowser/prohelp/index.html?overview2.htm) 

#### XnViewMP
['Compare' tool (forum)](https://forum.xnview.com/viewtopic.php?t=22667) (2011) with [screenshot](https://1.img-dpreview.com/files/p/TS560x560~forums/66402366/b2c30e2518ab482b8ae0e11ea5b36d3d) 


### Constrain panning

#### OpenSeadragon
[`visibilityRatio` option (demo)](https://openseadragon.github.io/examples/ui-zoom-and-pan/) 


### General user experience

#### OpenSeadragon, Blender, Adobe Lightroom, IIPMooViewer
Minimal and unobstructed viewport appearance with dark background and overall theme 

#### Windows 10
Glowing square buttons in the Start menu 

#### Microsoft Teams
Outline around video panel to indicate who is talking during a call 


# License
<!--- If you're not sure which open license to use see https://choosealicense.com/--->

Butterfly Viewer is made available under the [GNU GPL v3.0<sup>↗</sup>](https://www.gnu.org/licenses/gpl-3.0.en.html) license or later. For the full-text, see the `LICENSE.txt` file in the root directory of the Viewer's GitHub [repo<sup>↗</sup>](https://github.com/olive-groves/butterfly_viewer).