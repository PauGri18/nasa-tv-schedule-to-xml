#
import pdfplumber
import pandas as pd
import pytz
import datetime as dt
import os
from datetime import datetime, time
import sys
import unidecode
import time


##
## xmlcreateX.sh <pdfname.pdf>
##
##   prints
##      start datetime | description | end datetime
##
##   writes
##      pdfname.xml
##



def processpdf(apdf):

    xmlfilename = os.path.splitext(pdffilename)[0]
    xmlfilename = xmlfilename + '.xml'
    xmlout = open(xmlfilename, 'w')

    # XML channel block
    xmlout.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    xmlout.write('<tv generator-info-name="xmltv.co.uk" source-info-name="xmltv.co.uk" >\n')
    xmlout.write('<channel id="304">\n')
    xmlout.write('<display-name>NASA TV Live</display-name>\n')
    xmlout.write('</channel>\n')

    xmlout.write('\n')


    ## loop through all pages
    pc = 1
    for pn in apdf.pages:
        # convert page to table
        daytable = pn.extract_table()

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
            print('\nError: {0} page {1} - invalid page width!\n'.format(pdffilename, pc))
            time.sleep(3)
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
            print(pn, dayRowNo, ' ',    sep=', ', end='')


## ------------------------

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

                print(page_date_time.strftime('%d/%m/%Y %H:%M %z'),   sep=', ', end='')



## ------------------------


                # description col
                dayColNo = 1

                coltext = dayrow[dayColNo]
                coltext = str(coltext).replace('\n', '')

                # remove unicode characters
                progDesc = unidecode.unidecode(coltext)

                print(' | ', progDesc, ' | ',   sep='', end='')



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
                    coltext = str(coltext).replace('\n', '')
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

                    enddate = pagedate
                    end_date_time = dt.datetime.strptime(enddate +  ' ' + hh + ':' + mm + ' ' + ampm, '%m/%d/%Y %I:%M %p')

                except IndexError:
                    # End of page, assume finish at midnight today
                    enddate = pagedate
                    end_date_time = dt.datetime.strptime(enddate, '%m/%d/%Y') + dt.timedelta(days=1)



                # Localize
                end_date_time = est.localize(end_date_time)

                # save
                print(end_date_time.strftime('%d/%m/%Y %H:%M %z'),   sep=', ', end='\n')


                shortprogDesc = CreateShortDesc(progDesc)


                # XML program block
                xmlout.write('<programme start="{0}00 {1}" stop="{2}00 {3}" channel="304">\n'.format( \
                    page_date_time.strftime('%Y%m%d%H%M'), \
                    page_date_time.strftime('%z'), \
                    end_date_time.astimezone(est).strftime('%Y%m%d%H%M'), \
                    end_date_time.astimezone(est).strftime('%z')))
                xmlout.write('<title lang="en">{0}</title>\n'.format(shortprogDesc.rstrip()))
                xmlout.write('<desc lang="en">{0}</desc>\n'.format(progDesc.rstrip()))
                xmlout.write('</programme>\n')
                #
                # dayColNo==1
                #

            #
            # dayrowNo > 2
            #



## --------------------------



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
    # End of file
    #
    xmlout.write('</tv>\n')

    xmlout.close()

    print('Created: ', xmlfilename)



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
        if (len(w) >= 3):
            spd = ' '.join(w[0:3])   # join first 4 words with spaces
        else:
            spd = progDesc
    return spd



#------------------------------------------------------------------------------------------------
# Start
#------------------------------------------------------------------------------------------------
#os.system('clear')
est = pytz.timezone('US/Eastern')

# Command line parameters
if __name__ == "__main__":
    # sys.argv[0]=python filename
    if (len(sys.argv) > 1):
        # get path for pdf files
        directory_in_str = sys.argv[1]
    else:
        # assume currect directory
        directory_in_str = os.path.dirname(os.path.realpath(__file__))



# Process all pdfs on spcified path
filecount = 0
directory = os.fsencode(directory_in_str)
for file in os.listdir(directory):
     filename = os.fsdecode(file)

     if filename.lower().endswith(".pdf"):

        pdffilename = directory_in_str + "/" + filename

        starttime = datetime.now()
        try:
            pdf = pdfplumber.open(pdffilename)
            print('Pages: ', len(pdf.pages))

            processpdf(pdf)
            filecount += 1

            pdf.close

            endtime = datetime.now()
            runtime = endtime - starttime

        except IOError:
            print('Error: File {0} does not exist.'.format(pdffilename))

        finally:
            print('Start: {0}   End: {1}   Runtime: {2:5.2f}s'.format(
                starttime.strftime("%H:%M:%S"),
                endtime.strftime("%H:%M:%S"),
                runtime.total_seconds()) )


print('\n{0} PDF files converted to XML {1}'.format(filecount, directory_in_str))
