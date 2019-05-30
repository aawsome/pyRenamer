# -*- coding: utf-8 -*-

"""
Copyright (C) 2006-2008 Adolfo González Blázquez <code@infinicode.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

If you find any bugs or have any suggestions email: code@infinicode.org
"""

import os
import dircache
import glob
import re
import sys
from datetime import datetime, timedelta, time
import random
import unicodedata

import pyrenamer_globals

import exifread

if pyrenamer_globals.have_hachoir:
    from pyrenamer_metadata import PyrenamerMetadataMusic

if pyrenamer_globals.have_eyed3:
    import eyeD3

from gettext import gettext as _

STOP = False

def set_stop(stop):
    """ Set stop var to see if ther's no need to keep reading files """
    global STOP
    STOP = stop


def get_stop():
    return STOP


def escape_pattern(pattern):
    """ Escape special chars on patterns, so glob doesn't get confused """
    pattern = pattern.replace('[', '[[]')
    return pattern


def get_file_listing(dir, mode, pattern=None):
    """ Returns the file listing of a given directory. It returns only files.
    Returns a list of [file,/path/to/file] """

    filelist = []

    if  pattern == (None or ''):
        listaux = dircache.listdir(dir)
    else:
        if dir != '/': dir += '/'
        dir = escape_pattern(dir + pattern)
        listaux = glob.glob(dir)

    listaux.sort(key=str.lower)
    for elem in listaux:
        if STOP: return filelist
        if mode == 0:
            # Get files
            if not os.path.isdir(os.path.join(dir,elem)):
                filelist.append([os.path.basename(elem),os.path.join(dir,elem)])
        elif mode == 1:
            # Get directories
            if os.path.isdir(os.path.join(dir,elem)):
                filelist.append([os.path.basename(elem),os.path.join(dir,elem)])
        elif mode == 2:
            # Get files and directories
            filelist.append([os.path.basename(elem),os.path.join(dir,elem)])
        else:
            # Get files
            if not os.path.isdir(os.path.join(dir,elem)):
                filelist.append([os.path.basename(elem),os.path.join(dir,elem)])

    return filelist


def get_file_listing_recursive(dir, mode, pattern=None):
    """ Returns the file listing of a given directory recursively.
    It returns only files. Returns a list of [file,/path/to/file] """

    filelist = []

    # Get subdirs
    for root, dirs, files in os.walk(dir, topdown=False):
        if STOP: return filelist
        for directory in dirs:
            if STOP: return filelist
            elem = get_file_listing(os.path.join(root, directory), mode, pattern)
            for i in elem:
                if STOP: return filelist
                filelist.append(i)

    # Get root directory files
    list = get_file_listing(dir, mode, pattern)
    for i in list:
        filelist.append(i)

    return filelist


def get_dir_listing(dir):
    """ Returns the subdirectory listing of a given directory. It returns only directories.
     Returns a list of [dir,/path/to/dir] """

    dirlist = []

    listaux = dircache.listdir(dir)
    listaux.sort(key=str.lower)
    for elem in listaux:
        if STOP: return dirlist
        if os.path.isdir(os.path.join(dir,elem)): dirlist.append([os.path.basename(elem),os.path.join(dir,elem)])

    return dirlist


def get_new_path(name, path):
    """ Remove file from path, so we have only the dir"""
    dirpath = os.path.split(path)[0]
    if dirpath != '/': dirpath += '/'
    return dirpath + name


def replace_spaces(name, path, mode):
    """ if mode == 0: ' ' -> '_'
        if mode == 1: '_' -> ' '
        if mode == 2: '_' -> '.'
        if mode == 3: '.' -> ' '
        if mode == 4: ' ' -> '-'
        if mode == 5: '-' -> ' ' """

    name = unicode(name)
    path = unicode(path)

    if mode == 0:
        newname = name.replace(' ', '_')
    elif mode == 1:
        newname = name.replace('_', ' ')
    elif mode == 2:
        newname = name.replace(' ', '.')
    elif mode == 3:
        newname = name.replace('.', ' ')
    elif mode == 4:
        newname = name.replace(' ', '-')
    elif mode == 5:
        newname = name.replace('-', ' ')

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def replace_capitalization(name, path, mode):
    """ 0: all to uppercase
    1: all to lowercase
    2: first letter uppercase
    3: first letter uppercase of each word """
    name = unicode(name)
    path = unicode(path)

    if mode == 0:
        newname = name.upper()
    elif mode == 1:
        newname = name.lower()
    elif mode == 2:
        newname = name.capitalize()
    elif mode == 3:
        #newname = name.title()
        newname = ' '.join([x.capitalize() for x in name.split()])

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def replace_with(name, path, orig, new):
    """ Replace all occurences of orig with new """
    newname = name.replace(orig, new)
    newpath = get_new_path(newname, path)

    return unicode(newname), unicode(newpath)


def replace_accents(name, path):
    """ Remove accents, umlauts and other locale symbols from words 

    For instance: 'áàäâăÁÀÄÂĂéèëêěÉÈËÊĚíìïîĭÍÌÏÎĬóòöôŏÓÒÖÔŎúùüûůÚÙÜÛŮšŠčČřŘžŽýÝ'
    becomes:      'aaaaaAAAAAeeeeeEEEEEiiiiiIIIIIoooooOOOOOuuuuuUUUUUsScCrRzZyY'
    
    Standard ASCII characters don't change, such as:
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-`!@#$%^&*(){}[]:;.<>,'
    """
    name = unicode(name)
    path = unicode(path)


    newname = ''.join((c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn'))

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def replace_duplicated(name, path):
    """ Remove duplicated symbols """

    name = unicode(name)
    path = unicode(path)

    symbols = ['.', ' ', '-', '_']

    newname = name[0]
    for c in name[1:]:
        if c in symbols:
            if newname[-1] != c:
                newname += c
        else:
            newname += c

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def rename_using_patterns(name, path, pattern_ini, pattern_end, count):
    """ This method parses te patterns given by the user and stores the new filename
    on the treestore. Posibble patterns are:

    {#} Numbers
    {L} Letters
    {C} Characters (Numbers & letters, not spaces)
    {X} Numbers, letters, and spaces
    {@} Trash
    """
    name = unicode(name)
    path = unicode(path)

    pattern = pattern_ini
    newname = pattern_end

    pattern = pattern.replace('.','\.')
    pattern = pattern.replace('[','\[')
    pattern = pattern.replace(']','\]')
    pattern = pattern.replace('(','\(')
    pattern = pattern.replace(')','\)')
    pattern = pattern.replace('?','\?')
    pattern = pattern.replace('{#}', '([0-9]*)')
    pattern = pattern.replace('{L}', '([a-zA-Z]*)')
    pattern = pattern.replace('{C}', '([\S]*)')
    pattern = pattern.replace('{X}', '([\S\s]*)')
    pattern = pattern.replace('{@}', '(.*)')

    repattern = re.compile(pattern)
    try:
        groups = repattern.search(name).groups()

        for i in range(len(groups)):
            newname = newname.replace('{'+`i+1`+'}',groups[i])
    except:
        return None, None

    # Replace {num} with item number.
    # If {num2} the number will be 02
    # If {num3+10} the number will be 010
    count = `count`
    cr = re.compile("{(num)([0-9]*)}"
                    "|{(num)([0-9]*)(\+)([0-9]*)}")
    try:
        cg = cr.search(newname).groups()
        if len(cg) == 6:

            if cg[0] == 'num':
                # {num2}
                if cg[1] != '': count = count.zfill(int(cg[1]))
                newname = cr.sub(count, newname)

            elif cg[2] == 'num' and cg[4] == '+':
                # {num2+5}
                if cg[5] != '': count = str(int(count)+int(cg[5]))
                if cg[3] != '': count = count.zfill(int(cg[3]))

        newname = cr.sub(count, newname)
    except:
        pass

    # Replace {dir} with directory name
    dir = os.path.dirname(path)
    dir = os.path.basename(dir)
    newname = newname.replace('{dir}', dir)

    # Some date replacements
    newname = newname.replace('{date}', datetime.strftime(datetime.now(), "%d%b%Y"))
    newname = newname.replace('{year}', datetime.strftime(datetime.now(), "%Y"))
    newname = newname.replace('{month}', datetime.strftime(datetime.now(), "%m"))
    newname = newname.replace('{monthname}', datetime.strftime(datetime.now(), "%B"))
    newname = newname.replace('{monthsimp}', datetime.strftime(datetime.now(), "%b"))
    newname = newname.replace('{day}', datetime.strftime(datetime.now(), "%d"))
    newname = newname.replace('{dayname}', datetime.strftime(datetime.now(), "%A"))
    newname = newname.replace('{daysimp}', datetime.strftime(datetime.now(), "%a"))

    print "This routine is running!"

    # Some pattern matches for creation and modification date
    createdate, modifydate = get_filestat_data(get_new_path(name, path))
    if createdate is not None:
        newname = newname.replace('{createdate}', datetime.strftime(createdate, "%d%b%Y"))
        newname = newname.replace('{createyear}', datetime.strftime(createdate, "%Y"))
        newname = newname.replace('{createmonth}', datetime.strftime(createdate, "%m"))
        newname = newname.replace('{createmonthname}', datetime.strftime(createdate, "%B"))
        newname = newname.replace('{createmonthsimp}', datetime.strftime(createdate, "%b"))
        newname = newname.replace('{createday}', datetime.strftime(createdate, "%d"))
        newname = newname.replace('{createdayname}', datetime.strftime(createdate, "%A"))
        newname = newname.replace('{createdaysimp}', datetime.strftime(createdate, "%a"))
    else:
        newname = newname.replace('{createdate}', '')
        newname = newname.replace('{createyear}', '')
        newname = newname.replace('{createmonth}', '')
        newname = newname.replace('{createmonthname}', '')
        newname = newname.replace('{createmonthsimp}', '')
        newname = newname.replace('{createday}', '')
        newname = newname.replace('{createdayname}', '')
        newname = newname.replace('{createdaysimp}', '')

    if modifydate is not None:
        newname = newname.replace('{modifydate}', datetime.strftime(modifydate, "%d%b%Y"))
        newname = newname.replace('{modifyyear}', datetime.strftime(modifydate, "%Y"))
        newname = newname.replace('{modifymonth}', datetime.strftime(modifydate, "%m"))
        newname = newname.replace('{modifymonthname}', datetime.strftime(modifydate, "%B"))
        newname = newname.replace('{modifymonthsimp}', datetime.strftime(modifydate, "%b"))
        newname = newname.replace('{modifyday}', datetime.strftime(modifydate, "%d"))
        newname = newname.replace('{modifydayname}', datetime.strftime(modifydate, "%A"))
        newname = newname.replace('{modifydaysimp}', datetime.strftime(modifydate, "%a"))
    else:
        newname = newname.replace('{modifydate}', '')
        newname = newname.replace('{modifyyear}', '')
        newname = newname.replace('{modifymonth}', '')
        newname = newname.replace('{modifymonthname}', '')
        newname = newname.replace('{modifymonthsimp}', '')
        newname = newname.replace('{modifyday}', '')
        newname = newname.replace('{modifydayname}', '')
        newname = newname.replace('{modifydaysimp}', '')

    # Replace {rand} with random number between 0 and 100.
    # If {rand500} the number will be between 0 and 500
    # If {rand10-20} the number will be between 10 and 20
    # If you add ,5 the number will be padded with 5 digits
    # ie. {rand20,5} will be a number between 0 and 20 of 5 digits (00012)
    rnd = ''
    cr = re.compile("{(rand)([0-9]*)}"
                    "|{(rand)([0-9]*)(\-)([0-9]*)}"
                    "|{(rand)([0-9]*)(\,)([0-9]*)}"
                    "|{(rand)([0-9]*)(\-)([0-9]*)(\,)([0-9]*)}")
    try:
        cg = cr.search(newname).groups()
        if len(cg) == 16:

            if cg[0] == 'rand':
                if cg[1] == '':
                    # {rand}
                    rnd = random.randint(0,100)
                else:
                    # {rand2}
                    rnd = random.randint(0,int(cg[1]))

            elif cg[2] == 'rand' and cg[4] == '-' and cg[3] != '' and cg[5] != '':
                # {rand10-100}
                rnd = random.randint(int(cg[3]),int(cg[5]))

            elif cg[6] == 'rand' and cg[8] == ',' and cg[9] != '':
                if cg[7] == '':
                    # {rand,2}
                    rnd = str(random.randint(0,100)).zfill(int(cg[9]))
                else:
                    # {rand10,2}
                    rnd = str(random.randint(0,int(cg[7]))).zfill(int(cg[9]))

            elif cg[10] == 'rand' and cg[12] == '-' and cg[14] == ',' and cg[11] != '' and cg[13] != '' and cg[15] != '':
                # {rand2-10,3}
                rnd = str(random.randint(int(cg[11]),int(cg[13]))).zfill(int(cg[15]))

        newname = cr.sub(str(rnd), newname)
    except:
        pass

    # Returns new name and path
    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def replace_images(name, path, newname, newpath, correction):
    """ Pattern replace for images """

    name = unicode(name)
    path = unicode(path)
    newname = unicode(newname)
    newpath = unicode(newpath)

    # Image EXIF replacements
    date, width, height, cameramaker, cameramodel = get_exif_data(get_new_path(name, path))
  
    try:
        delta = timedelta(seconds=float(correction))
        date = date + delta
    except:
        pass

    if date != None:
        newname = newname.replace('{imagedate}', datetime.strftime(date, "%d%b%Y"))
        newname = newname.replace('{imageyear}', datetime.strftime(date, "%Y"))
        newname = newname.replace('{imagemonth}', datetime.strftime(date, "%m"))
        newname = newname.replace('{imagemonthname}', datetime.strftime(date, "%B"))
        newname = newname.replace('{imagemonthsimp}', datetime.strftime(date, "%b"))
        newname = newname.replace('{imageday}', datetime.strftime(date, "%d"))
        newname = newname.replace('{imagedayname}', datetime.strftime(date, "%A"))
        newname = newname.replace('{imagedaysimp}', datetime.strftime(date, "%a"))
        newname = newname.replace('{imagetime}', datetime.strftime(date, "%H_%M_%S"))
        newname = newname.replace('{imagehour}', datetime.strftime(date, "%H"))
        newname = newname.replace('{imageminute}', datetime.strftime(date, "%M"))
        newname = newname.replace('{imagesecond}', datetime.strftime(date, "%S"))
    else:
        newname = newname.replace('{imagedate}','')
        newname = newname.replace('{imageyear}', '')
        newname = newname.replace('{imagemonth}', '')
        newname = newname.replace('{imagemonthname}', '')
        newname = newname.replace('{imagemonthsimp}', '')
        newname = newname.replace('{imageday}', '')
        newname = newname.replace('{imagedayname}', '')
        newname = newname.replace('{imagedaysimp}', '')
        newname = newname.replace('{imagetime}', '')
        newname = newname.replace('{imagehour}', '')
        newname = newname.replace('{imageminute}', '')
        newname = newname.replace('{imagesecond}', '')

    if width != None: newname = newname.replace('{imagewidth}', width)
    else: newname = newname.replace('{imagewidth}', '')

    if height != None: newname = newname.replace('{imageheight}', height)
    else: newname = newname.replace('{imageheight}', '')

    if cameramaker != None: newname = newname.replace('{cameramaker}', cameramaker)
    else: newname = newname.replace('{cameramaker}', '')

    if cameramodel != None: newname = newname.replace('{cameramodel}', cameramodel)
    else: newname = newname.replace('{cameramodel}', '')

    # Returns new name and path
    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def get_filestat_data(path):
    """ Get file status attributes from a file. """
    createdate = None
    modifydate = None

    try:
        st = os.stat(path)
        if not st:
            print "ERROR: File attributes could not be read", path
            return createdate, modifydate
    except:
        print "ERROR: processing file attributes on", path
        return createdate, modifydate

    createdate = datetime.fromtimestamp(st.st_ctime).timetuple()
    modifydate = datetime.fromtimestamp(st.st_mtime).timetuple()

    return createdate, modifydate 

def get_exif_data(path):
    """ Get EXIF data from file. """
    date = None
    width = None
    height = None
    cameramaker = None
    cameramodel = None

    try:
        file = open(path, 'rb')
    except:
        print "ERROR: Opening image file", path
        return date, width, height, cameramaker, cameramodel

    try:
        tags = exifread.process_file(file)
        if not tags:
            print "ERROR: No EXIF tags on", path
            return date, width, height, cameramaker, cameramodel
    except:
        print "ERROR: proccesing EXIF tags on", path
        return date, width, height, cameramaker, cameramodel

    # tags['EXIF DateTimeOriginal'] = "2001:03:31 12:27:36"
    if tags.has_key('EXIF DateTimeOriginal'):
        data = str(tags['EXIF DateTimeOriginal'])
        try:
            date = datetime.strptime(data, "%Y:%m:%d %H:%M:%S")
        except:
            date = None

    if tags.has_key('EXIF ExifImageWidth'):
        width = str(tags['EXIF ExifImageWidth'])

    if tags.has_key('EXIF ExifImageLength'):
        height = str(tags['EXIF ExifImageLength'])

    if tags.has_key('Image Make'):
        cameramaker = str(tags['Image Make'])

    if tags.has_key('Image Model'):
        cameramodel = str(tags['Image Model'])

    return date, width, height, cameramaker, cameramodel



def replace_music_hachoir(name, path, newname, newpath):
    """ Pattern replace for music """

    file = get_new_path(name, path)

    try:
        tags = PyrenamerMetadataMusic(file)

        artist = clean_metadata(tags.get_artist())
        album  = clean_metadata(tags.get_album())
        title  = clean_metadata(tags.get_title())
        track  = clean_metadata(tags.get_track_number())
        trackt = clean_metadata(tags.get_track_total())
        genre  = clean_metadata(tags.get_genre())
        year   = clean_metadata(tags.get_year())

        if artist != None: newname = newname.replace('{artist}', artist)
        else: newname = newname.replace('{artist}', '')

        if album != None: newname = newname.replace('{album}', album)
        else: newname = newname.replace('{album}', '')

        if title != None: newname = newname.replace('{title}', title)
        else: newname = newname.replace('{title}', '')

        if track != None: newname = newname.replace('{track}', str(track).zfill(2))
        else: newname = newname.replace('{track}', '')

        if trackt != None: newname = newname.replace('{tracktotal}', str(trackt).zfill(2))
        else: newname = newname.replace('{tracktotal}', '')

        if genre != None: newname = newname.replace('{genre}', genre)
        else: newname = newname.replace('{genre}', '')

        if year != None: newname = newname.replace('{myear}', year)
        else: newname = newname.replace('{myear}', '')

    except:
        newname = newname.replace('{artist}', '')
        newname = newname.replace('{album}', '')
        newname = newname.replace('{title}', '')
        newname = newname.replace('{track}', '')
        newname = newname.replace('{tracktotal}', '')
        newname = newname.replace('{genre}', '')
        newname = newname.replace('{myear}', '')

    # Returns new name and path
    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)

def replace_music_eyed3(name, path, newname, newpath):
    """ Pattern replace for mp3 """

    file = get_new_path(name, path)

    if eyeD3.isMp3File(file):
        try:
            audioFile = eyeD3.Mp3AudioFile(file, eyeD3.ID3_ANY_VERSION)
            tag = audioFile.getTag()
        except Exception, e:
            print "ERROR eyeD3:", e
            newpath = get_new_path('', path)
            return '', unicode(newpath)

        try:
            artist = clean_metadata(tag.getArtist())
        except Exception, e:
            print "ERROR eyeD3:", e
            artist = None

        try:
            album  = clean_metadata(tag.getAlbum())
        except Exception, e:
            print "ERROR eyeD3:", e
            album = None

        try:
            title  = clean_metadata(tag.getTitle())
        except Exception, e:
            print "ERROR eyeD3:", e
            title = None

        try:
            track  = clean_metadata(tag.getTrackNum()[0])
        except Exception, e:
            print "ERROR eyeD3:", e
            track = None

        try:
            trackt = clean_metadata(tag.getTrackNum()[1])
        except Exception, e:
            print "ERROR eyeD3:", e
            trackt = None

        try:
            genre  = clean_metadata(tag.getGenre().getName())
        except Exception, e:
            print "ERROR eyeD3:", e
            genre = None

        try:
            year   = clean_metadata(tag.getYear())
        except Exception, e:
            print "ERROR eyeD3:", e
            year = None

        if artist != None: newname = newname.replace('{artist}', artist)
        else: newname = newname.replace('{artist}', '')

        if album != None: newname = newname.replace('{album}', album)
        else: newname = newname.replace('{album}', '')

        if title != None: newname = newname.replace('{title}', title)
        else: newname = newname.replace('{title}', '')

        if track != None: newname = newname.replace('{track}', str(track))
        else: newname = newname.replace('{track}', '')

        if trackt != None: newname = newname.replace('{tracktotal}', str(trackt))
        else: newname = newname.replace('{tracktotal}', '')

        if genre != None: newname = newname.replace('{genre}', genre)
        else: newname = newname.replace('{genre}', '')

        if year != None: newname = newname.replace('{myear}', year)
        else: newname = newname.replace('{myear}', '')
    else:
        newname = newname.replace('{artist}', '')
        newname = newname.replace('{album}', '')
        newname = newname.replace('{title}', '')
        newname = newname.replace('{track}', '')
        newname = newname.replace('{tracktotal}', '')
        newname = newname.replace('{genre}', '')
        newname = newname.replace('{myear}', '')

    # Returns new name and path
    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def rename_file(ori, new):
    """ Change filename with the new one """

    if ori == new:
        return True, None    # We don't need to rename the file, but don't show error message

    if os.path.exists(new):
        print _("Error while renaming %s to %s! -> %s already exists!") % (ori, new, new)
        error = "[Errno 17] %s" % os.strerror(17)
        return False, error

    try:
        os.renames(ori, new)
        print "Renaming %s to %s" % (ori, new)
        return True, None
    except Exception, e:
        print _("Error while renaming %s to %s!") % (ori, new)
        print e
        return False, e


def insert_at(name, path, text, pos):
    """ Append text at given position"""
    if pos >= 0:
        ini = name[0:pos]
        end = name[pos:len(name)]
        newname = ini + text + end
    else:
        newname = name + text

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def delete_from(name, path, ini, to):
    """ Delete chars from ini till to"""
    textini = name[0:ini]
    textend = name[to+1:len(name)]
    newname = textini + textend

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)

def cut_extension(name, path):
    """ Remove extension from file name """

    if '.' in name:
        ext = name.split('.')[-1]
        name = name[0:len(name)-len(ext)-1]
        path = path[0:len(path)-len(ext)-1]
        return name, path, ext
    else:
        return name, path, ''

def add_extension(name, path, ext):
    """ Add extension to file name """

    if ext != '' and ext != None and name != '' and name != None:
        name = name + '.' + ext
        path = path + '.' + ext
    return name, path


def clean_metadata(tag):
    """ Removes reserver characters from a given filename """
    try:
        tag = tag.replace('|', '')
        tag = tag.replace('/', '')
        tag = tag.replace('\\', '')
        tag = tag.replace('?', '')
        tag = tag.replace('%', '')
        tag = tag.replace('*', '')
        tag = tag.replace(':', '')
        tag = tag.replace('<', '')
        tag = tag.replace('>', '')
        tag = tag.replace('"', '')
        return tag
    except:
        return None
