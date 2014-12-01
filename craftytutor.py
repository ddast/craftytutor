#!/usr/bin/env python3

##########################################################################
# craftytutor.py - Command-line driven tutorial group managment          #
#                                                                        #
# This program is free software: you can redistribute it and/or modify   #
# it under the terms of the GNU General Public License as published by   #
# the Free Software Foundation, either version 3 of the License, or      #
# (at your option) any later version.                                    #
#                                                                        #
# This program is distributed in the hope that it will be useful,        #
# but WITHOUT ANY WARRANTY; without even the implied warranty of         #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
# GNU General Public License for more details.                           #
#                                                                        #
# You should have received a copy of the GNU General Public License      #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
##########################################################################

import sys
import shutil
import readline
import cmd
import argparse
import os.path
import xml.etree.ElementTree as ET

import stringcompleter.stringcompleter as stringcompleter


class CraftyTutor(cmd.Cmd):

    ####################################################################
    # Overload funtions of cmd.Cmd                                     #
    ####################################################################

    intro = ("Hello crafty tutor. How may I be of assistance?\n"
        + "Type help or ? to list commands.\n")

    def emptyline(self):
        """Don't do anything if command is empty."""
        pass

    def __init__(self, sheets, group):
        """Initialize the CraftyTutor

        @sheets: filename of the XML file of the sheets
        @group: filename of the XML file of the group
        """
        cmd.Cmd.__init__(self)
        self.sheetsfile = sheets
        self.groupfile = group
        # backup if file exists else initialize new files
        if os.path.exists(sheets):
            shutil.copyfile(sheets, sheets + ".old")
        else:
            print("Creating new sheets file, use newsheet <arg> to fill.\n")
            self.init_xml(sheets)
        newsheet = False
        if os.path.exists(group):
            shutil.copyfile(group, group + ".old")
        else:
            print("Creating new group file...")
            self.init_xml(group)
            newsheet = True
        # parse the files 
        self.do_reload(None)
        if newsheet:
            self.settitles()
            print("Use 'addstudents' to fill.\n")

    def precmd(self, line):
        """Unset command autocompletion inside the commands."""
        self.oldcompleter = readline.get_completer()
        self.oldcompleterdelims = readline.get_completer_delims()
        readline.set_completer_delims('')
        self.set_empty_completion()
        return line

    def postcmd(self, stop, line):
        """Reset command autocompletion before returning."""
        readline.set_completer(self.oldcompleter)
        readline.set_completer_delims(self.oldcompleterdelims)
        return stop

    ####################################################################
    # Implement commands                                               #
    ####################################################################

    def do_addstudents(self, arg):
        "Add students to the current group."
        self.addstudents()
        self.update_names()

    def do_addids(self, arg):
        "Add/change the student ids (Matrikelnummer)."
        self.addids()

    def do_newsheet(self, arg):
        "Enter the data of a new problem sheet."
        self.newsheet()

    def do_ratesheet(self, arg):
        "Enter score of the sheet <arg>."
        self.ratesheet(arg)

    def do_presented(self, arg):
        "Enter persons which presented problem of sheet <arg>."
        self.presented(arg)

    def do_write(self, arg):
        "Write changes to file."
        indent(self.root_group)
        self.tree_group.write(self.groupfile, encoding='unicode',
                xml_declaration=True)
        indent(self.root_sheets)
        self.tree_sheets.write(self.sheetsfile, encoding='unicode',
                xml_declaration=True)

    def do_reload(self, arg):
        "Reload files (discard unsaved changes)"
        self.tree_sheets = ET.parse(self.sheetsfile)
        self.tree_group = ET.parse(self.groupfile)
        self.root_sheets = self.tree_sheets.getroot()
        self.root_group = self.tree_group.getroot()
        self.update_names()

    def do_print(self, arg):
        "Create a LaTeX file with table for sheet <arg>"
        self.print_table(arg)

    def do_quit(self, arg):
        "Quit the crafty tutor."
        return ask_yes_no("Are you sure?", 'no')

    ####################################################################
    # Member functions implementing functionality                      #
    ####################################################################

    def init_xml(self, filename):
        """Initialize a xml file with an empty data block."""
        root = ET.Element('data')
        tree = ET.ElementTree(root)
        tree.write(filename)

    def update_names(self):
        """Update the global list 'names'."""
        self.names = []
        xnames = self.root_group.findall('./student/name')
        for xn in xnames:
            self.names.append(xn.text)

    def set_empty_completion(self):
        """Switch off readline completion."""
        completer = stringcompleter.StringCompleter([])
        readline.set_completer(completer.complete)

    def set_name_completion(self):
        """Use readline completion for the students names."""
        completer = stringcompleter.StringCompleter(self.names)
        readline.set_completer(completer.complete)

    def get_sheet(self, sheet):
        """Get the xml tree of a sheet."""
        if not sheet:
            print("Specify sheet number.")
            return
        lcursheet = self.root_sheets.findall("./sheet[@no='{}']".format(sheet))
        if len(lcursheet) == 0:
            print("Sheet not defined. Use 'newsheet' first.")
            return
        if len(lcursheet) > 1:
            print("More than one sheet with number {}.".format(sheet),
                    "Fix that!")
            return
        return lcursheet[0]

    def settitles(self):
        """Set title and subtitle of a new group."""
        try:
            title = input("Title: ")
            subtitle = input("Subtitle (will be expanded by sheet no): ")
        except:
            print()
            return
        xtitle = ET.SubElement(self.root_group, 'title')
        xtitle.text = title
        xsubtitle = ET.SubElement(self.root_group, 'subtitle')
        xsubtitle.text = subtitle

    def addstudents(self):
        """Add students and ids til empty name is entered."""
        print("Return at empty name")
        while True:
            try:
                name = input("Name: ")
            except:
                print()
                return
            if not len(name):
                break
            try:
                studid = input("ID:   ")
            except:
                print()
                return
            # new element
            newstud = ET.Element('student')
            # add name
            xname = ET.SubElement(newstud, 'name')
            xname.text = name
            # add board
            xboard = ET.SubElement(newstud, 'board')
            xboard.text = '0'
            # add id
            xstudid = ET.SubElement(newstud, 'id')
            if len(studid):
                xstudid.text = studid
            # add to root
            self.root_group.append(newstud)

    def addids(self):
        """Manipulate or add student ids."""
        for student in self.root_group.findall('student'):
            print(student.find('name').text)
            studid = student.find('id')
            try:
                if studid.text:
                    newid = input_def('ID', studid.text)
                else:
                    newid = input("ID: ")
            except:
                print()
                return
            studid.text = newid

    def newsheet(self):
        """Interatively add a new problem sheet."""
        # get highest sheet number
        print("Return with Ctrl+D")
        no = 0
        for sheets in self.root_sheets.findall('sheet'):
            try:
                curno = int(sheets.attrib['no'])
            except ValueError:
                continue
            if curno > no:
                no = curno
        # ask for number
        try:
            no = input_def("Number", no+1)
        except:
            print()
            return

        # create element
        xsheet = ET.Element('sheet', {'no': no})

        # get highest problem number
        probno = 0
        for probs in self.root_sheets.iter('prob'):
            try:
                curprob = int(probs.attrib['no'])
            except ValueError:
                continue
            if curprob > probno:
                probno = curprob
        # ask for problems
        while True:
            try:
                iprobno = int(probno)
            except ValueError:
                iprobno = 0
            try:
                probno = input_def("\nProblem", iprobno+1)
                while True:
                    probtype = input_def("Type", 'v')
                    if probtype in "vw":
                        break
                    print("Only v and w allowed as type")
                while True:
                    probpoints = input("Points: ")
                    if len(probpoints) and probpoints.isdigit():
                        break
                    print("Enter Points (only digits allowed)")
            except EOFError:
                print()
                break
            except:
                print()
                return
            xprob = ET.SubElement(xsheet, 'prob',
                    {'no': probno, 'type': probtype})
            xprob.text = probpoints

        # add to root
        self.root_sheets.append(xsheet)

    def ratesheet(self, sheet):
        """Interactively rate the given sheet."""
        cursheet = self.get_sheet(sheet)
        if not cursheet:
            return
        print("Rate sheet no {}. Be gentle!".format(sheet))

        # ask which problems should be rated
        prob_numbers = []
        for prob in cursheet.findall('prob'):
            prob_no = prob.attrib['no']
            do_rate = ask_yes_no("Rate problem {}({})?".format(
                prob_no, prob.attrib["type"]), 'yes')
            if do_rate:
                prob_numbers.append(prob_no)
        # break if no problems are rated
        if not prob_numbers:
            return

        # iterate over all students and ask for scores
        for stud in self.root_group.findall('student'):
            print("\n{}".format(stud.find('name').text))
            # create new sheet item
            xsheet = ET.Element('sheet', {'no': cursheet.attrib['no']})
            # iterate over all probs of the sheet
            for prob in cursheet.findall('prob'):
                probno = prob.attrib['no']
                # rate problem
                if probno in prob_numbers:
                    maxscore = prob.text
                    xprob = ET.SubElement(xsheet, 'prob', {'no': probno})
                    # loop until valid value is given
                    while True:
                        try:
                            score = input_def("Problem {}".format(probno),
                                    maxscore)
                        except:
                            print()
                            return
                        # consistency check
                        try:
                            fscore = float(score)
                        except ValueError:
                            print("Only numbers allowed")
                            continue
                        if fscore > float(maxscore):
                            print("Score is greater than maximal score")
                            continue
                        break
                    # store score
                    xprob.text = score
                # or keep old entry
                else:
                    xprob = ET.SubElement(xsheet, 'prob', {'no': probno})
                    xprob.text = text_or_none(
                            stud.find("./sheet[@no='{}']/prob[@no='{}']".format(
                                sheet, probno)))
            # delete existing
            lold = stud.findall("./sheet[@no='{}']".format(sheet))
            for old in lold:
                stud.remove(old)
            # add to student
            stud.append(xsheet)

    def presented(self, sheet):
        """Interactively ask who presented the problems."""
        cursheet = self.get_sheet(sheet)
        if not cursheet:
            return
        print("Enter presenters of sheet no {}.".format(sheet))
        # use name completion
        self.set_name_completion()
        # iterate over all problems
        problems = cursheet.findall('./prob')
        for prob in problems:
            while True:
                try:
                    presenter = input("Problem {}: ".format(prob.attrib['no']))
                except:
                    print()
                    return
                if presenter in self.names:
                    break
                if not presenter:
                    break
                print("Unknown student. Stop making up names!")
            if not presenter:
                continue
            # increase number of presented problems
            xboard = self.root_group.findall(
                    "./student[name='{}']/board".format(presenter))
            if len(xboard) != 1:
                print("Panic!")
                return
            xboard[0].text = str(int(xboard[0].text) + 1)

    def get_total_points(self, problemtype):
        """Count total points of given problemtype

        @problemtype: either 'w' or 'v' for written or voted problems
        """
        probs = self.root_sheets.findall(
                "./sheet/prob[@type='{}']".format(problemtype))
        total = 0.0
        for prob in probs:
            total += float(prob.text)
        return total

    def get_points(self, sheet, problemtype):
        """Count total points of given problemtype of a sheet.

        @sheet: sheet number
        @problemtype: either 'w' or 'v' for written or voted problems
        """
        probs = self.root_sheets.findall(
                "./sheet[@no='{}']/prob[@type='{}']".format(sheet,
                    problemtype))
        total = 0.0
        for prob in probs:
            total += float(prob.text)
        return total

    def get_points_of_stud(self, stud):
        """Count the total points of student.

        Return both written and voted scores.
        """
        total_w = 0.0
        total_v = 0.0
        # iterate over all problems
        sheets = stud.findall('sheet')
        for sheet in sheets:
            sheet_no = sheet.attrib['no']
            probs = sheet.findall('prob')
            for prob in probs:
                prob_no = prob.attrib['no']
                # get type
                prob_type = self.root_sheets.find(
                        "./sheet[@no='{}']/prob[@no='{}']".format(
                            sheet_no, prob_no)).attrib['type']
                # sum up
                score = float(prob.text)
                if prob_type == 'w':
                    total_w += score
                elif prob_type == 'v':
                    total_v += score
        # return total scores
        return total_w, total_v

    def print_table(self, sheet):
        """Create the LaTeX file."""
        # get current sheet
        xsheet = self.get_sheet(sheet)
        if not xsheet:
            return
        # what shoud be added to the table?
        print_id = ask_yes_no("Add students ID (Matrikelnummer)?", 'no')
        print_percent = ask_yes_no("Add score overview?", 'yes')
        if print_percent:
            print_cur_w = ask_yes_no(
                    "Include written points of current sheet?", 'yes')
            print_cur_v = ask_yes_no(
                    "Include vote points of current sheet?", 'no')
        total_written = self.get_total_points('w')
        total_vote = self.get_total_points('v')
        if print_percent and not print_cur_w:
            total_written -= self.get_points(sheet, 'w')
        if print_percent and not print_cur_v:
            total_vote -= self.get_points(sheet, 'v')
        # get titles
        title = self.root_group.find('title').text
        subtitle = self.root_group.find('subtitle').text
        # open file
        filename = "{}_sheet{}.tex".format(self.groupfile.replace(".xml", ""),
                sheet)
        ftable = open(filename, 'w')

        # write header
        ftable.write("\\documentclass[%\n  ")
        if not print_id:
            ftable.write("%")
        ftable.write("matrikelnummer,\n  ")
        if not print_percent:
            ftable.write("%")
        ftable.write("punktestand\n]{exTable}\n\n")
        # write body
        ftable.write("\\begin{document}\n\n")
        ftable.write("\\exTitle({})\n\\exSubtitle({}{})\n\n".format(
            title, subtitle, sheet))
        ftable.write("\\setHandInPoints({:.6g})\n\\setVotePoints({:.6g})\n"
                .format(total_written, total_vote))
        # write problems
        for prob in xsheet.findall('prob'):
            ftable.write("\\addProblem(A{})({})\n".format(
                prob.attrib['no'], prob.attrib['type']))
        # write students
        for stud in self.root_group.findall('student'):
            # general info
            ftable.write("\\addStudent({})({})({})".format(
                text_or_none(stud.find('name')),
                text_or_none(stud.find('id')),
                text_or_none(stud.find('board')))
                )
            # percentage of score
            scores = self.get_points_of_stud(stud)
            try:
                perc_w = 100.*scores[0]/total_written
            except ZeroDivisionError:
                perc_w = 100.
            try:
                perc_v = 100.*scores[1]/total_vote
            except ZeroDivisionError:
                perc_v = 100.
            ftable.write("({:.2f})({:.2f})".format(perc_v, perc_w))
            # score of current sheet
            for prob in xsheet.findall('prob'):
                ftable.write("({})".format(
                    text_or_none(
                        stud.find("./sheet[@no='{}']/prob[@no='{}']".format(
                            sheet, prob.attrib['no']))
                        )))
            ftable.write("\n")
        # finish
        ftable.write("\n\\makeTable\n\n\\end{document}")
        # close file
        ftable.close()


########################################################################
# Top-level helper functions                                           #
########################################################################

# taken from http://effbot.org/zone/element-lib.htm#prettyprint
def indent(elem, level=0):
    """In-place prettyprint formatter."""
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def input_def(prompt, default):
    """Prompt for a value and return default if input is empty."""
    tmp = input('{} [{}]: '.format(prompt, default))
    if len(tmp):
        return tmp
    else:
        return str(default)


def ask_yes_no(question, default):
    """Ask a yes or no question.

    @question: String containing the question.
    @default: The default answer (either 'yes' or 'no')
    """
    yes_vals = ['y', 'ye', 'yes']
    no_vals  = ['n', 'no']
    if default.lower() == 'yes':
        prompt = "[Y/n]"
        yes_vals.append('')
    elif default.lower() == 'no':
        prompt = "[y/N]"
        no_vals.append('')
    else:
        return
    while True:
        try:
            answer = input("{} {} ".format(question, prompt))
        except:
            print()
            return False
        if answer.lower() in yes_vals:
            return True
        if answer.lower() in no_vals:
            return False


def text_or_none(xmltree):
    """Return either the text of the xmltree or '' if it is None."""
    if xmltree is None:
        return ""
    elif xmltree.text is None:
        return ""
    else:
        return xmltree.text


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Manage students scores")
    parser.add_argument('sheets', help="XML file of the problem sheets")
    parser.add_argument('group', help="XML file of the group")
    args = parser.parse_args()

    # set readline options
    readline.parse_and_bind('set editing-mode vi')

    # fire up the CraftyTutor
    ct = CraftyTutor(args.sheets, args.group)
    ct.cmdloop()


if __name__ == '__main__':
    main()

