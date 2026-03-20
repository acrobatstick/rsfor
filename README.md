# rsfor

rsfor is a tool for creating online rallies on [RallySimFans](https://rallysimfans.hu).

## Pre-requisites

To ensure the program is running as exactly as it is. You need to install:

- Python 3.4+
- Google Chrome

### Installation

If you don't have git installed you can first download the source code
[right here](https://github.com/acrobatstick/rsfor/archive/refs/heads/main.zip).
After everything is set, you can go inside the source code folder and do:

```bash
pip install .
```

## Usage

```bash
# Create online rally based on the existing rally
rsfor -i <LINK TO ONLINE RALLY> run --dump

# Create online rally with your own configuration by providing flag -i with
# your configuration file path. see /examples for configuration example
rsfor -i ./examples/1.yaml run

# Preview configuration before creating them
rsfor -i ./examples/1.yaml preview

# Dumps configuration to a yaml file that can be reused anytime
rsfor -i <LINK TO ONLINE RALLY> dump
```

For detailed usage, you can use `rsfor --help`.

## Configurations

You can refer to this tables if you want to create your own rally configurations.

### Group/Car IDs

| ID  | Name                             |
| --- | -------------------------------- |
| 10  | WRC 1.6                          |
| 11  | WRC 2.0                          |
| 21  | Group 2                          |
| 22  | Group 4                          |
| 23  | Group A5                         |
| 78  | Group A6                         |
| 24  | Group A7                         |
| 30  | Group A8                         |
| 31  | Group B                          |
| 32  | Group N4                         |
| 33  | Group R1                         |
| 34  | Group R2                         |
| 35  | Group R3                         |
| 36  | Group R4                         |
| 37  | Group R5                         |
| 38  | Group RGT                        |
| 71  | Super 1600                       |
| 111 | Super 2000                       |
| 118 | Rally 5                          |
| 104 | Rally 4                          |
| 108 | Rally 3                          |
| 125 | Rally 2                          |
| 113 | Abarth Grande Punto S2000        |
| 102 | Alpine A110 Rally RGT            |
| 81  | Aston Martin Vantage RGT         |
| 91  | Audi 200 quattro GrpA            |
| 85  | Audi quattro A1 GrpB             |
| 86  | Audi quattro A2 GrpB             |
| 26  | Audi quattro Grp4                |
| 87  | Audi Sport quattro GrpB          |
| 122 | BMW M1 GrpB                      |
| 107 | BMW M3 E30 GrpA                  |
| 110 | BMW M3 E36 GrpA                  |
| 72  | Citroen C2 GT S1600              |
| 44  | Citroen C2 R2 Max                |
| 88  | Citroen C3 R5                    |
| 18  | Citroen C3 WRC 2017              |
| 16  | Citroen C4 WRC 2008              |
| 42  | Citroen DS3 R1                   |
| 49  | Citroen DS3 R3-MAX               |
| 68  | Citroen DS3 R5                   |
| 12  | Citroen DS3 WRC                  |
| 116 | Citroen Xsara Kit Car            |
| 17  | Citroen Xsara WRC 2006           |
| 57  | Fiat 124 Abarth Rally RGT        |
| 25  | Fiat 126 Grp2                    |
| 123 | Fiat 131 Abarth Grp4             |
| 120 | Fiat Abarth 500 R3T              |
| 97  | Ford Escort Mk II RS Grp4        |
| 60  | Ford Escort Mk V RS Cosworth Grp |
| 114 | Ford Fiesta Mk VI S2000          |
| 90  | Ford Fiesta Mk VIII R2           |
| 45  | Ford Fiesta R2                   |
| 54  | Ford Fiesta R5                   |
| 100 | Ford Fiesta Rally2               |
| 109 | Ford Fiesta Rally3               |
| 133 | Ford Fiesta rally3 evo           |
| 99  | Ford Fiesta Rally4               |
| 13  | Ford Fiesta RS WRC 2014          |
| 15  | Ford Fiesta WRC 2019             |
| 73  | Ford Focus Mk II RS WRC 2006     |
| 50  | Honda Civic Type R(FN2) R3       |
| 19  | Hyundai i20 Coupe WRC 2017       |
| 95  | Hyundai i20 Coupe WRC 2020       |
| 128 | Hyundai i20 Coupe WRC 2021       |
| 126 | Hyundai i20 N Rally2             |
| 55  | Hyundai i20 R5                   |
| 79  | Lada Kalina RC2 GrpA             |
| 58  | Lada VFTS GrpB                   |
| 92  | Lancia Delta HF 4WD GrpA         |
| 103 | Lancia Stratos HF Grp4           |
| 83  | Lotus Exige S RGT                |
| 93  | Mazda 323 BF 4WD Turbo GrpA      |
| 124 | Mini JCW WRC                     |
| 66  | Mitsubishi Lancer Evo II GrpA    |
| 41  | Mitsubishi Lancer Evo IX N4      |
| 65  | Mitsubishi Lancer Evo IX R4      |
| 74  | Mitsubishi Lancer Evo X R4       |
| 46  | Opel ADAM R2                     |
| 27  | Opel Ascona 400 Grp4             |
| 84  | Opel Manta 400 GrpB              |
| 106 | Peugeot 106 Rallye S20 GrpA      |
| 89  | Peugeot 205 T16 GrpB             |
| 112 | Peugeot 207 S2000 Evolution Plus |
| 47  | Peugeot 208 R2                   |
| 105 | Peugeot 208 Rally4               |
| 127 | Peugeot 208 T16 R5               |
| 117 | Peugeot 306 Maxi Kit Car         |
| 82  | Porsche 911 GT3 RS (2007) RGT    |
| 67  | Porsche 911 GT3 RS (2010) RGT    |
| 69  | Porsche 911 SC 3.0 Grp4          |
| 40  | Porsche 911 SC RS GrpB           |
| 61  | Renault 5 GT Turbo GrpA          |
| 29  | Renault Clio 16S Williams GrpA   |
| 51  | Renault Clio III R3              |
| 52  | Renault Clio IV R3T              |
| 132 | Renault Clio Rally3              |
| 115 | Renault Clio Rally4              |
| 119 | Renault Clio Rally5              |
| 43  | Renault Twingo R1                |
| 48  | Renault Twingo R2 Evo            |
| 98  | Seat Leon Cupra R GrpN           |
| 80  | Skoda 130 LR GrpB                |
| 76  | Skoda 130 RS Grp2                |
| 56  | Skoda Fabia R5                   |
| 59  | Skoda Fabia R5 evo               |
| 130 | Skoda Fabia RS Rally2            |
| 121 | Skoda Fabia S2000 Evo 2          |
| 101 | Skoda Fabia WRC 2006             |
| 77  | Skoda Favorit 136 L GrpA         |
| 39  | Subaru Impreza GC8 555 GrpA      |
| 75  | Subaru Impreza GDA WRC2003 (S9)  |
| 64  | Subaru Impreza N14 N4            |
| 53  | Subaru Impreza N15 R4            |
| 70  | Toyota Celica 2000GT(ST185) GrpA |
| 96  | Toyota Celica TCT (TA64) GrpB    |
| 131 | Toyota GR Yaris Rally2           |
| 20  | Toyota Yaris WRC 2018            |
| 28  | Trabant P 800 RS GrpA            |
| 129 | Volvo 240 Turbo GrpA             |
| 94  | VW Golf II GTI 16V GrpA          |
| 62  | VW Polo GTI R5                   |
| 14  | VW Polo R WRC 2016               |
| 63  | Wartburg 353 W 460 GrpA          |

### Stage Data

[https://rallysimfans.hu/rbr/stages.php](https://rallysimfans.hu/rbr/stages.php)

### Damage Levels

| ID | Name |
| -- | ---- |
| 2 | Reduced |
| 3 | Realistic |

### Stage Length

Stage Length must be >= 2 <= 69

### Leg Length

Leg Length must be >= 1 <= 6

### Pacenote Options

| ID | Name |
| -- | ---- |
| 0 | Normal Pacenotes |
| 1 | Don't show 3D pacenotes |
| 2 | Don't show the countdown of pacenote distance |
| 3 | Don't show the the 3D pacenote and countdown of pace note distance |
| 4 | Only pacenote audio |
| 12 | No pacenote symbols and audio |

### Mechanic Skill

| ID | Skill |
| -- | ----- |
| 1 | Inexperienced |
| 2 | Proficient |
| 3 | Competent |
| 4 | Skilled |
| 5 | Expert |

### Road Service Minutes

| ID | Minutes |
| -- | ------- |
| 0 | No service |
| 2 | 2 minutes |
| 3 | 3 minutes |
| 5 | 5 minutes |

### Stage Surfaces

| ID | Surface |
| -- | ------- |
| 1  | tarmac  |
| 2  | gravel  |
| 3  | snow    |

### Stage Surface Wear

| ID | Wear Status |
| -- | ----------- |
| -1 | Auto |
| 1 | New |
| 2 | Normal |
| 3 | Worn |

### Stage Wetness

| ID | Wetness |
| -- | ------- |
| -1 | Auto |
| 1 | Dry |
| 2 | Damp |
| 3 | Wet |

### Set Tyre

| ID | Name |
| -- | ---- |
| -1 | Auto |
| 0 | Tarmac Dry |
| 1 | Tarmac Intermediate |
| 2 | Tarmac Wet |
| 3 | Gravel Dry |
| 4 | Gravel Intermediate |
| 5 | Gravel Wet |
| 6 | Snow |
| 7 | Keep Previous |

### Stage Weathers

- Evening Clear Crisp
- Evening Clear Hazy
- Evening Clear LightFog
- Evening Clear LightRain
- Evening Clear NoRain
- Evening Clear NoSnow
- Evening HeavyCloud Hazy
- Evening HeavyCloud HeavyFog-1
- Evening HeavyCloud HeavyRain
- Evening HeavyCloud HeavySnow
- Evening HeavyCloud LightFog
- Evening HeavyCloud LightRain
- Evening HeavyCloud LightSnow
- Evening HeavyCloud NoRai
- Evening HeavyCloud NoSnow
- Evening LightCloud Crisp
- Evening LightCloud Hazy
- Evening LightCloud LightFog
- Evening LightCloud LightRain
- Evening LightCloud LightSnow
- Evening LightCloud NoRain
- Evening LightCloud NoSnow
- Evening PartCloud Crisp
- Evening PartCloud Hazy
- Evening PartCloud HeavyFog
- Evening PartCloud LightFog
- Morning Clear Crisp
- Morning Clear Hazy
- Morning Clear HeavyFog
- Morning Clear HeavyRai
- Morning Clear LightFog
- Morning Clear LightRain
- Morning Clear NoRain
- Morning HeavyCloud Hazy
- Morning HeavyCloud HeavyFog
- Morning HeavyCloud HeavyRain
- Morning HeavyCloud HeavySnow
- Morning HeavyCloud LightFog
- Morning HeavyCloud LightRain
- Morning HeavyCloud LightSnow
- Morning HeavyCloud NoRain
- Morning HeavyCloud NoSnow
- Morning LightCloud Crisp
- Morning LightCloud Hazy
- Morning LightCloud HeavyFog
- Morning LightCloud HeavyRain
- Morning LightCloud LightFog
- Morning LightCloud LightRain
- Morning LightCloud NoRain
- Morning LightCloud NoSnow
- Morning PartCloud Crisp
- Morning PartCloud Hazy
- Morning PartCloud HeavyRain
- Morning PartCloud LightFog
- Morning PartCloud LightRain
- Morning PartCloud NoRain
- Morning PartCloud NoSnow
- Noon Clear Crisp
- Noon Clear Hazy
- Noon Clear HeavyFog
- Noon HeavyCloud Crisp
- Noon HeavyCloud Hazy
- Noon HeavyCloud HeavyFog
- Noon HeavyCloud HeavyRain
- Noon HeavyCloud HeavySnow
- Noon HeavyCloud LightFog
- Noon HeavyCloud LightRain
- Noon HeavyCloud LightSnow
- Noon HeavyCloud NoRain
- Noon HeavyCloud NoSnow
- Noon LightCloud Crisp
- Noon LightCloud Hazy
- Noon LightCloud HeavyFog
- Noon LightCloud LightFog
- Noon LightCloud LightRain
- Noon LightCloud LightSnow
- Noon LightCloud NoRain
- Noon LightCloud NoSnow
- Noon PartCloud Crisp
- Noon PartCloud Hazy
- Noon PartCloud LightSnow
- Noon PartCloud NoRain

## Contributing

Go ahead. I'm pretty sure there's plenty to fix since this is my first
time building with Python or you can add new feature that we can benefit
from it.
