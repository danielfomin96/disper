#!/usr/bin/env python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
        
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License at http://www.gnu.org/licenses/gpl.txt
# By using, editing and/or distributing this software you agree to
# the terms and conditions of this license.

import sys
import logging
import optparse

import switcher

# program name and version
progname = 'disper'
progver = '0.1'


def get_resolutions_display(sw, disp):
    '''return a set of resolution for the specified display'''
    r = sw.get_display_res(disp)
    if len(r)==0:
        r = set(['800x600','640x480'])
        logging.warning('no resolutions found for display %s, falling back to default'%disp)
    return r

def get_resolutions(sw, displays = []):
    '''return an array of resolution-sets for each display connected'''
    if len(displays) == 0:
        displays = sw.get_displays()
    res = []
    for disp in displays:
        res.append(get_resolutions_display(sw, disp))
    return res

def get_common_resolutions(res):
    '''return a list of common resolutions from an array of resolution-sets
    as returned by get_resolutions(). return value is sorted from high to
    low.'''
    commonres = res[0]
    for n in range(1,len(res)):
        commonres.intersection_update(res[n])
    commonres = list(commonres)
    commonres.sort(_resolutions_sort)
    commonres.reverse()
    return commonres


def _resolutions_sort(a, b):
    '''sort function for resolution strings in the form "WxH", sorts
    by number of pixels W*H.'''
    ax,ay = map(int, a.partition('x')[::2])
    bx,by = map(int, b.partition('x')[::2])
    return ax*ay - bx*by


def do_main():
    '''main program entry point'''
    ### option defitions
    usage = "usage: %prog [options] (-l|-s|-c)"
    version = ' '.join(map(str, [progname, progver]))
    parser = optparse.OptionParser(usage, version=version)
    parser.set_defaults(resolution='auto', displays='auto', debug=logging.WARNING)

    parser.add_option('-v', '--verbose', action='store_const', dest='debug', const=logging.INFO,
        help='show what\'s happening')
    parser.add_option('-q', '--quiet', action='store_const', dest='debug', const=logging.ERROR,
        help='be quiet and only show errors')
    parser.add_option('-r', '--resolution', dest='resolution',  
        help='set resolution, or "auto" to detect')
    parser.add_option('-d', '--displays', dest='displays',
        help='comma-separated list of displays to operate on, or "auto" to detect')

    group = optparse.OptionGroup(parser, 'Actions',
        'Select exactly one of the following actions')
    group.add_option('-l', '--list', action='append_const', const='list', dest='actions',
        help='list the attached displays')
    group.add_option('-s', '--single', action='append_const', const='single', dest='actions',
        help='only enable the primary display')
    group.add_option('-c', '--clone', action='append_const', const='clone', dest='actions',
        help='clone displays')
    parser.add_option_group(group)

    (options, args) = parser.parse_args()
    logging.getLogger().setLevel(options.debug)
    if not options.actions: options.actions = []
    if len(options.actions) == 0:
        logging.info('no action specified')
        # show help if no action specified
        parser.print_help()
        sys.exit(0)
    elif len(options.actions) > 1:
        parser.error('conflicting actions, please specify exactly one action: '
                     +', '.join(options.actions))
        sys.exit(2)

    ### autodetect and apply options
    sw = switcher.Switcher()

    # determine displays involved
    if 'single' in options.actions:
        if options.displays == 'auto':
            options.displays = sw.get_primary_display()
        elif options.displays != [sw.get_primary_display()]:
            logging.warning('cloning specified displays instead of selecting primary display only')
        options.actions = ['clone']
    if options.displays == 'auto':
        options.displays = sw.get_displays()
        logging.info('auto-detected displays: '+', '.join(options.displays))
    else:
        options.displays = map(lambda x: x.strip(), options.displays.split(','))
        logging.info('using specified displays: '+', '.join(options.displays))

    ### execute action
    if 'list' in options.actions:
        # list displays with resolutions
        for disp in options.displays:
            res = get_resolutions_display(sw, disp)
            logres = list(res)
            logres.sort(_resolutions_sort)
            logres.reverse()
            print 'display %s: %s'%(disp, sw.get_display_name(disp))
            print ' resolutions: '+', '.join(logres)
    elif 'clone' in options.actions:
        # determine resolution
        resolution = options.resolution
        if resolution == 'auto':
            res = get_resolutions(sw, options.displays)
            commonres = get_common_resolutions(res)
            if len(commonres)==0:
                logging.critical('displays share no common resolution')
                sys.exit(1)
            resolution = commonres[0]
        # and switch
        sw.switch_clone(resolution, options.displays)
    else:
        logging.critical('program error, unrecognised action: '+', '.join(options.actions))
        sys.exit(2)

def main():
    logging.basicConfig(level=logging.WARNING, format='%(message)s')
    try:
        do_main()
    except Exception,e:
        logging.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()

# vim:ts=4:sw=4:expandtab: