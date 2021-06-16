#
import pdfplumber
import pandas as pd
import pytz
import datetime as dt
import os
from datetime import datetime, time,  date, timedelta
import sys
import unidecode
import time

import requests
import os.path



##
## xmlcreateX.sh <pdfname.pdf> | <Path>
##
##   debug (<pdffile>.txt)
##      start datetime | description | end datetime
##
##   writes (stdout)
##      xml import format
##



def xmlHeader():
    # XML channel block
    print('<?xml version="1.0" encoding="UTF-8"?>',
          '<tv generator-info-name="xmltv.co.uk" source-info-name="xmltv.co.uk" >',
          '<channel id="304">',
          '<display-name>NASA TV Live</display-name>',
          '</channel>', sep='\n', end='\n\n', file=xmlout)



def xmlfooter():
    print('</tv>\n', file=xmlout)



def CreateShortDesc(progDesc):
    # truncate long titles
    if (progDesc.find(':') >= 0):
        w = progDesc.split(':')
        spd = w[0]
    elif (progDesc.find('-') >= 0):
        w = progDesc.split('-')
        spd = w[0]
    else:
        w = progDesc.split(' ')
        if (len(w) >= 2):
            spd = ' '.join(w[0:2])   # join first 3 words with spaces
        else:
            spd = progDesc
    return spd



def processpdf(apdf):
    ## loop through all pages
    pc = 1
    for pg in apdf.pages:
        # convert page to table
        daytable = pg.extract_table()

        dayRowNo = 0

        #
        # pdf format:
        #
        # page
        #   title
        #             | day - date |
        #   time ampm | desc       | time ampm



        # Bad page formatting from NASA - single column - ignore page
        if (len(daytable[dayRowNo]) < 2):
            print('\nError: page {0} - invalid page width!\n'.format(pc), file=debugout)
            continue



        while (dayRowNo < len(daytable)):

            # extract row
            dayrow = daytable[dayRowNo]



            if (pc == 1) and (dayRowNo == 1):
                #
                # On page 1, extract day - date in col 1
                #
                if (dayrow[1] != ''):
                    # removes spaces and split DAY - DATE
                    daydate = dayrow[1].replace(' ', '').split('-')

                    # Get day, date as string
                    #pageday = daydate[0]
                    pagedate = daydate[1]



            # print pageno, line
            print(pg, dayRowNo, ' ',   sep=', ', end='', file=debugout)

# ------------------------

            # each column in table
            dayColNo = 0

            coltext = dayrow[dayColNo]
            coltext = str(coltext).replace('\n', '')

            # not a header
            if (dayRowNo > 2):

                # 0 = time column

                # remove '.' in time columns
                coltext = str(coltext).replace('.', '')

                # split HH:MM and am/pm
                coltime = coltext.split(' ')

                # split HH:MM
                hourmin = coltime[0].split(':')
                hh = hourmin[0]

                # Might be HH or HH:MM
                mm = '0'
                ## mm exists
                if (len(hourmin) > 1):
                    mm = hourmin[1]

                # get am/pm
                ampm = coltime[1]

                # merge pagedate + time + ampm
                page_date_time = dt.datetime.strptime(pagedate +  ' ' + hh + ':' + mm + ' ' + ampm, '%m/%d/%Y %I:%M %p')
                page_date_time = est.localize(page_date_time)

                print(page_date_time.strftime('%d/%m/%Y %H:%M %z'),   sep=', ', end='', file=debugout)

# ------------------------

                # description col
                dayColNo = 1

                coltext = dayrow[dayColNo]
                coltext = str(coltext).replace('\n', '')

                # Remove unicode characters
                progDesc = unidecode.unidecode(coltext)
                # Escape control codes
                progDesc = progDesc.replace('<', '&lt;') \
                    .replace('&', '&amp;') \
                    .replace('>', '&gt;') \
                    .replace('"', '&quot;') \
                    .replace("'", '&apos;')

                print(' | ', progDesc, ' | ',   sep='', end='', file=debugout)



                # ------------------------------------
                # End date from start date of next row
                # ------------------------------------

                # if double line on last page row, dayRowNo+1 will raise exception
                try:
                    # look forward if desc is blank
                    # this might be past end of page
                    while ( (dayRowNo < len(daytable)) \
                        and ( (daytable[dayRowNo+1][1] is None) or (daytable[dayRowNo+1][1] == "")) ):
                        dayRowNo += 1

                    # Look at next row, get time from 1st column
                    dayrow = daytable[dayRowNo+1]

                    # split time string HHpm or HH:MMpm
                    coltext = dayrow[0]

                    # remove junk
                    coltext = str(coltext).replace('\n', '').replace('.', '')

                    # split HH:MM and am/pm
                    coltime = coltext.split(' ')

                    # split HH:MM
                    hourmin = coltime[0].split(':')
                    hh = hourmin[0]

                    # Might be HH or HH:MM
                    mm = '0'
                    ## mm exists
                    if (len(hourmin) > 1):
                        mm = hourmin[1]

                    # get am/pm
                    ampm = coltime[1]

                    enddate = pagedate
                    end_date_time = dt.datetime.strptime(enddate +  ' ' + hh + ':' + mm + ' ' + ampm, '%m/%d/%Y %I:%M %p')

                except IndexError:
                    # End of page, assume finish at midnight today
                    enddate = pagedate
                    end_date_time = dt.datetime.strptime(enddate, '%m/%d/%Y') + dt.timedelta(days=1)



                # Localize
                end_date_time = est.localize(end_date_time)

                # save
                print(end_date_time.strftime('%d/%m/%Y %H:%M %z'),   sep=', ', end='\n', file=debugout)

                # XML program block
                print('<programme start="{0}00 {1}" stop="{2}00 {3}" channel="304">'.format(
                    page_date_time.strftime('%Y%m%d%H%M'),
                    page_date_time.strftime('%z'),
                    end_date_time.astimezone(est).strftime('%Y%m%d%H%M'),
                    end_date_time.astimezone(est).strftime('%z')),
                    file=xmlout)
                print('<title lang="en">{0}</title>'.format(CreateShortDesc(progDesc).rstrip()), file=xmlout)
                print('<desc lang="en">{0}</desc>'.format(progDesc.rstrip()), file=xmlout)
                print('</programme>', file=xmlout)
                #
                # dayColNo==1
                #

            else:
                # dayrowNo > 2, print a newline
                print('', file=debugout)

            #
            # Last column
            #
            dayRowNo += 1

        #
        # End of page
        #



        # inc existing pagedate
        page_date_time = dt.datetime.strptime(pagedate, '%m/%d/%Y')
        page_date_time += dt.timedelta(days=1)
        pagedate = page_date_time.strftime('%m/%d/%Y')

        pc += 1

    #
    # End of pdf file
    #



#------------------------------------------------------------------------------------------------
# Start
#------------------------------------------------------------------------------------------------

est = pytz.timezone('US/Eastern')



# ------------------------

# main url
#   url='https://www.nasa.gov/multimedia/nasatv/schedule.html'
#
# files stored at
#   url = 'https://www.nasa.gov/sites/default/files/atoms/files'
#
# filenames in the format "m-d-yyyy"
#   fn = 'nasa-tv-schedule-for-week-of-6-7-2021.pdf'

today = date.today()
idx = (today.weekday() + 1) % 7   # MON = 0, SUN = 6 -> SUN = 0 .. SAT = 6
##print('idx=',idx)

# dd/mm/YY -> last sunday
d1 = (today - timedelta(days=idx-1))
url = 'https://www.nasa.gov/sites/default/files/atoms/files'


lastsunday = "{0}-{1}-{2}".format(d1.month, d1.day, d1.year)
##print('Last Sunday = ', lastsunday)
fn = 'nasa-tv-schedule-for-week-of-{0}.pdf'.format(lastsunday)

r = requests.get(url + '/' + fn, \
        headers={'User-Agent': 'Mozilla/5.0'}, \
        allow_redirects=True, \
        verify=True)  # to get content after redirection

if (r.status_code == 200):
    # download and save
    with open(os.path.basename(r.url), 'wb') as f:
        f.write(r.content)

else:
    print('Error {0} not found'.format(r.url))
    #exit()



# ------------------------



# Command line parameters
if __name__ == "__main__":
    # sys.argv[0]=python filename
    if (len(sys.argv) > 1):
        # get path for pdf files
        directory_in_str = sys.argv[1]
    else:
        # assume currect directory
        directory_in_str = os.path.dirname(os.path.realpath(__file__))



# Process all pdfs on specified path
filecount = 0
directory = os.fsencode(directory_in_str)

xmlout=sys.stdout
xmlHeader()

for file in os.listdir(directory):
    filename = os.fsdecode(file)

    if filename.lower().endswith(".pdf"):

        pdffilename = os.path.join(directory_in_str, filename)

        debugfilename = os.path.splitext(pdffilename)[0]
        debugfilename = debugfilename + '.txt'
        debugout = open(debugfilename, 'w')


        starttime = datetime.now()
        try:
            #pdf = pdfplumber.open(pdffilename)
            ##print('Pages: {0}'.format(len(pdf.pages)), file=debugout)

            with pdfplumber.open(pdffilename) as pdf:
                processpdf(pdf)
                filecount += 1

            endtime = datetime.now()
            runtime = endtime - starttime

        except IOError:
            print('Error: File {0} does not exist'.format(pdffilename), file=debugout)

        except KeyboardInterrupt:
            print('\nControl-C pressed')
            sys.exit(0)

        finally:
            ##print('Start: {0}   End: {1}   Runtime: {2:5.2f}s'.format(
            ##    starttime.strftime("%H:%M:%S"),
            ##    endtime.strftime("%H:%M:%S"),
            ##    runtime.total_seconds()),
            ##    file=debugout)
            pass

    # if .pdf
# for all files

xmlfooter()

print('\n{0} PDF files converted to XML {1}'.format(filecount, directory_in_str), file=debugout)
