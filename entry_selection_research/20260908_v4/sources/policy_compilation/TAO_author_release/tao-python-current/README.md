<div align="center">
----------------------------------8<----------------------------------

(C) 2026 Rasul Kairgeldin and Miguel Á. Carreira-Perpiñán, UC Merced Machine Learning Group

https://faculty.ucmerced.edu/mcarreira-perpinan/research/TAO.html

----------------------------------8<----------------------------------
</div>

## Install Visual Studio Code IDE 

**Install Required VS Code Extensions:**
* Open VS Code 
* Go to the Extensions view (press Ctrl+Shift+X on Windows/Linux) 
* Search for and install the Python extension (published by Microsoft) 
* Search for and install the Jupyter extension (published by Microsoft) 

**Install conda:** 
```bash
sudo apt update
sudo apt install wget -y
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

You will know this was successful if you now see (base) prefixed at the beginning of your terminal prompt :
```bash
source ~/.bashrc
```

**Verify install:** 
```bash
conda --version
```

You currently see (base) version of conda environment. You can create environment for a project :
```bash
conda create --name tao-projects python=3.13
```

**To lists all environments:** 
```bash
conda env list
```

Activates environment "tao-projects". You will see (tao-projects) prefixed at the beginning of your terminal prompt :
```bash
conda activate tao-projects
```

Next, install all the necessary packages either manually in active conda environment :
```bash
conda install numpy
conda install scipy
conda install scikit-learn=1.7
conda install pandas
conda install matplotlib
conda install ipykernel
```

**To run tao:** 
```bash
python3 driver_TAO_classification.py --C_dnode=10 --depth=9 --alpha=0
python3 driver_TAO_regression.py --C_dnode=10 --depth=9 --alpha=0
```

<div align="center">

----------------------------------8<----------------------------------

The following web page contains our work about the Tree Alternating Optimization (TAO) algorithm:

https://faculty.ucmerced.edu/mcarreira-perpinan/research/TAO.html

If you use this code in your work, please cite the relevant paper from that web page.

----------------------------------8<----------------------------------

</div>