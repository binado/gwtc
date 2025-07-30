# gwtc

Fetch and manipulate public data from the GWTC catalogs.

## Installation


### With pixi (recommended)

1. Clone the repo with

```shell
git clone https://github.com/binado/phdrepo.git
```

2. Install [`pixi`](https://pixi.sh/dev/installation/#update), a package manager for conda and pypi

3. Run the command

```shell
pixi install -e dev
```
to install the dev environment with access to jupyter.

4. To run scripts, run

```shell
pixi run [scripts] --help
```

### With conda

1. Clone the repo with

```shell
git clone https://github.com/binado/phdrepo.git
```
2. Create a conda enviroment with

```shell
conda env create -f environment.yml
conda activate gwtc
```
4. Install the package locally with

```shell
python -m pip install -e .
```

The package scripts will be added to the PATH.

You can check available scripts in the [project config](./pyproject.toml).

## Downloading GWTC data products

Using [`zenodo_get`](https://github.com/dvolgyes/zenodo_get):

- For GWTC3:

``` shell
pip install zenodo_get
zenodo_get 8177023 -g "*_nocosmo.h5" -o [output_dir]
```

- For GWTC2.1:

``` shell
pip install zenodo_get
zenodo_get 6513631 -g "*_nocosmo.h5" -o [output_dir]
```

You may change the glob pattern to "*_cosmo.h5" if you are interested in the cosmologically reweighted samples (more info in the O3b catalog paper, see link below).

## Useful links

- [O3a paper](https://arxiv.org/abs/2010.14527)
- [O3b paper](https://arxiv.org/abs/2111.03606)

- [GWTC-3 data release](https://zenodo.org/records/5546663)
- [GWTC-2.1 data release](https://zenodo.org/records/6513631)

## Acknowledgements

We use the `pesummary` package for parsing the .h5 files.

[[docs]](https://docs.ligo.org/lscsoft/pesummary/stable/index.html) [[Paper]](https://arxiv.org/abs/2006.06639)
