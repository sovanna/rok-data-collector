# Rise of Kingdoms - Data Collector

**It allows to extract data from screenshots that you have to take yourself from the game.**

It is possible and I recommend that you use some *macros/tools/softwares* to do the screenshots automatically. You can do it manually but it can be time consuming hahaha.

> For example, I am on MacOS and I use the Automator App to automate screenshots captures. You may have some useful tools on Windows too.


## 1. Requirements

- [Tesseract](https://tesseract-ocr.github.io/tessdoc/#compiling-and-installation)
- Python3
- virtualenv

## 2. Installation

```
git clone git@github.com:sovanna/rok-data-collector.git
```
```
cd rok-data-collector/
```
```
virtualenv .venv
```
```
source .venv/bin/activate
```
```
pip install -r requirements.txt
```

## 3. How the program works

### a. First, take screenshots from the game.

- Start with the **MORE INFO** view

![MORE INFO View](./sample/screenshot-62478-62479.png)

- Then with the **GOVERNOR PROFILE** view and the **Kill Statistics** open

![MORE INFO View](./sample/screenshot-62483.png)

#### **Do this for all the governors you need, hence the automate tool to take screenshots**

### b. Put all screenshots inside the `screenshots` folder if not already saved inside it.

### c. Define coordinates for data areas you want to collect

**Check the `template.json` file, update it for your need. It should be self-explanatory.**

Basically, you need to determine a set of coordinates that consist of a rectangle around the data you want to collect:
- position X
- position Y
- width
- height

```
{
    "x": 562,
    "y": 332,
    "width": 222,
    "height": 37,
    "is_number": false,
    "key": "name"
}
```

**For example, use Photoshop. You can draw a rectangle selection and find with the info window the coordinate you need**

---
Below an example of a custom tool that I use for this.
![example of areas selection](./sample/Screenshot%202023-08-11%20at%2011.55.00%20AM.png)

**Once your template.json is set, you won't need to update it unless the Game UI changes**

## 4. Collect Data

>When your `template.json` and your `screenshots` are done, you can start the program to collect all data.

Open a Terminal,

```
cd rok-data-collector/
```
```
virtualenv .venv
```
```
source .venv/bin/activate
```
```
python main.py collect --using template.json --from-folder screenshots
```
**An excel file (*.xlsx) will be created at the end with all your data collected.**

*Note: If the program can't extract some data, it will mark "ERROR". You can look for "ERROR" in Excel to correct manually if needed.*

# Day to Day Data Collections

Well, when you have everything set, you will only:
- launch your automate tool to take screenshots (take a rest)
- launch the program (take a rest)
- correct "ERROR" if any in the excel (*.xlsx) file (optional)
- open the *.xlsx file, copy content, paste in Google Sheets for example
- enjoy or do your own post-processing that suit your needs for KvK

*There is almost no manual work, except the post-processing from the \*.xlsx file*