# -*- coding: utf-8 -*-

import pyglet
import string
import time
import unicodedata
import os
from alphabet_detector import AlphabetDetector
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from time import strftime
from twilio.rest import TwilioRestClient
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import ctypes
#import win32api
import urllib
ad = AlphabetDetector()
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]

                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value

    return exif_data


def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None


def _convert_to_degress(value):
    """Helper function to convert the GPS coordinates stored in the EXIF to degress in float format"""
    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)

    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)

    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)

    return d + (m / 60.0) + (s / 3600.0)


def get_lat_lon(exif_data):
    """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
    lat = None
    lon = None

    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]

        gps_latitude = _get_if_exist(gps_info, "GPSLatitude")
        gps_latitude_ref = _get_if_exist(gps_info, 'GPSLatitudeRef')
        gps_longitude = _get_if_exist(gps_info, 'GPSLongitude')
        gps_longitude_ref = _get_if_exist(gps_info, 'GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degress(gps_latitude)
            if gps_latitude_ref != "N":
                lat = 0 - lat

            lon = _convert_to_degress(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon
    return lat, lon

#**********  *****  MAIN  *****  **********

print(strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + " Skript spusten.")

#Start Firefox webdriver
prof = webdriver.FirefoxProfile()
prof.set_preference("browser.startup.homepage_override.mstone", "ignore")
prof.set_preference("startup.homepage_welcome_url.additional", "about:blank")


driver = webdriver.Firefox(prof)


'''
#driver = webdriver.PhantomJS(executable_path=r'C:\PhantomJS\bin\phantomjs.exe')
#Visit project-gc and forward to Groundspeak geocaching login page
driver.get("http://project-gc.com/Tools/NotLogged?country=Czech+Republic&submit=Filter")
#driver.get_screenshot_as_file('screen01.jpg')
driver.find_element_by_css_selector("a[href*='/User/Login']").click()
driver.find_element_by_css_selector("a[href*='/oauth.php']").click()

#Login
username = driver.find_element_by_id("Username")
password = driver.find_element_by_id("Password")
username.send_keys("python27")
password.send_keys("automatheslo")
driver.find_element_by_css_selector('.btn.btn-primary').click()

#Authenticate
driver.find_element_by_name("uxAllowAccessButton").click()
'''
gcCode = raw_input(strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + " Zadejte GC kod kese: ")

#gcCode = "GC73EXG"
#GC2E2PW filmovy let
#GC1PPBE hamlikov
#GC189E5 karluv most
#GC73EXG miminko mez dama
#GC379ZJ 2 stranky obrazku

print(strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + " Zpracovavam kes " + gcCode)


driver.get("https://coord.info/" + gcCode)

galleryLink = driver.find_element_by_xpath("/html/body/form[1]/section/div/div/div[5]/div[1]/p[1]/a[2]")
galleryLink.click()

rootDir = "d:\\generated\\exIFtractor\\"
cacheDir = rootDir + gcCode + "\\"

if not os.path.exists(cacheDir):
    print(strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + " Vytvarim slozku " + cacheDir)
    os.makedirs(cacheDir)
f = open(cacheDir + "coords.txt", 'w')
#/html/body/form[1]/section/div/div[1]/table/tbody/tr[1]/td[1]/a/img

count = 0
page = 0
nextPage = True
completed = False
while nextPage and not completed:
    page = page + 1
    print(strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + " Stranka " + str(page))


    tablesCount = len(driver.find_elements_by_xpath("/html/body/form[1]/section/div/div[1]/table"))
    if tablesCount == 1:
        picTableNum = 1
        nextPage = False
    elif tablesCount == 3:
        picTableNum = 2
    #print "pocet tabulek je", tablesCount
    rowsCount = len(driver.find_elements_by_xpath("/html/body/form[1]/section/div/div[1]/table[" + str(picTableNum) + "]/tbody/tr"))

    for i in range(1,rowsCount+1,1):
        if completed:
            break
        colsCount = len(driver.find_elements_by_xpath("/html/body/form[1]/section/div/div[1]/table[" + str(picTableNum) + "]/tbody/tr[" + str(i)  + "]/td"))
        for j in range(1, colsCount+1, 1):
            try:
                imgLink = driver.find_element_by_xpath("/html/body/form[1]/section/div/div[1]/table[" + str(picTableNum) + "]/tbody/tr[" + str(i) + "]/td[" + str(j) +"]/a").get_attribute("href")
                if imgLink[-3:] != "jpg" and imgLink[-4:] != "jpeg":        #'''osetrit nehledani exifu v neJPG souborech'''
                    continue
                urllib.urlretrieve(imgLink, cacheDir + str(page) + "_" + str(i) + "_" + str(j) + ".jpg")
                image = Image.open(cacheDir + str(page) + "_" + str(i) + "_" + str(j) + ".jpg")
                exif_data = get_exif_data(image)
                lat, lon = get_lat_lon(exif_data)
                if lat is not None and lon is not None:
                    print "                   ", imgLink
                    print "                   ", lat, lon
                    f.write(imgLink + "\n" + str(lat) + ", " + str(lon) + "\n")
                else:
                    print "                   ", "Zadne souradnice v exif"
            except NoSuchElementException, ex:
                print(strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + " Pravdepodobne posledni obrazek")
                completed = True
                break

            count = count + 1
    if tablesCount == 1:
        break
    elementCount = len(driver.find_elements_by_xpath("/html/body/form[1]/section/div/div[1]/table[1]/tbody/tr/td[2]/a"))
    #print "pocet zobrazenych klikatelnych stranek je", elementCount
    element = driver.find_element_by_xpath("/html/body/form[1]/section/div/div[1]/table[1]/tbody/tr/td[2]/a[" + str(elementCount) + "]")
    #mozna, jestli je to element 15
    classAtr = element.get_attribute("class")
    #print classAtr
    if classAtr != "aspNetDisabled":
        element.click()
    else:
        nextPage = False


    #/html/body/form[1]/section/div/div[1]/table[1]/tbody/tr/td[2]/a[7]
print(strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + " Stahnuto " + str(count) + " obrazku")
print(strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + " Konec")
driver.quit()
f.close()