# hophacks-2018

## About
This prototype was developed at the 2018 Johns Hopkins University Hackathon (HopHacks).  It is designed to address the theme of the hackathon: improving city life.

Navigational applications often prioritize speed when routing users, sometimes at the cost of safety.  This application presents safety as an additional routing factor, which does not significantly hinder speed; the slowest route suggested by the application cannot be less than half the speed of the fastest possible route.

Baltimore crime data is used to assess the safety of the possible routes, and the application selects the safest route to suggest.  
Data was acquired from https://catalog.data.gov/dataset/bpd-arrests-4f2eb and published by https://catalog.data.gov/dataset?publisher=data.baltimorecity.gov


## Usage
1. Execute the python script: crime_map.py
2. When prompted, select the baltimore_city_crime_data.csv file
3. Either enter custom coordinates or select preset destinations for source and destination addresses
4. Click "Go" to view the directions with an accompanying map
