#/usr/bin/env python

import sys
import os
import re
import getopt
import tkFileDialog

from numpy import *

SAVE_FILE_TYPES=[("space delimited",".prn"),
                 ("text",".txt"),
                 ("All files","*")]

class View:
    def __init__(self, label):
        self.label = label
        self.reglist = None
        self.datapointlist = []
        self.landmarklist = []
        self.linelist = []
        self.reglist = RegList()
        self.analyzed_landmarks = []
        self.analyzed_lines = []
        
    def add_datapoint(self, datapoint):
        self.datapointlist.append(datapoint)
        
    def add_line(self, line):
        self.linelist.append(line)
        
    def add_landmark(self, landmark):
        self.landmarklist.append(landmark)
        
    def reg_matrix(self):
        return self.reglist.as_matrix()
        
    def lines_matrix(self):
        points_list = []
        for line in self.linelist:
            points_list += line.as_list
        num_points = len(points_list)/3
        m = matrix(points_list)
        m.resize(num_points,3)
        return m
    
    def landmarks_matrix(self):
        points_list = []
        for landmark in self.landmarklist:
            points_list += landmark.as_list
        num_points = len(points_list)/3
        m = matrix(points_list)
        m.resize(num_points,3)
        return m
            
    def set_reg_points(self, label_list):
        new_list = []
        for datapoint in self.datapointlist:
            if datapoint.label in label_list:
                self.reglist.add_landmark(datapoint)
            else:
                new_list = new_list + [datapoint,]
        self.datapointlist = new_list    
    
    def labels(self):
        ret = []
        for datum in self.datapointlist:
            ret.append(datum.label)
        return ret
        
    def split_lines_and_landmarks(self):
        self.linelist = []
        self.landmarklist = []
        for datapoint in self.datapointlist:
            if len(datapoint.as_list) > 3:
                self.linelist.append(datapoint)
            else:
                self.landmarklist.append(datapoint)
        
    def update_landmarks(self, matrix):
        for index in range(0,len(self.landmarklist)):
            curr = Datapoint(self.landmarklist[index].label)
            curr.add_point(matrix[index].tolist()[0])
            self.analyzed_landmarks.append(curr)
              
    def update_lines(self, matrix):
        matrix_index = 0
        for index in range(0,len(self.linelist)):
            curr = Datapoint(self.linelist[index].label)
            line_size = len(self.linelist[index].as_list)
            end_index = matrix_index + line_size/3
            for i in range(matrix_index, end_index):
                curr.add_point(matrix[i].tolist()[0])
            self.analyzed_lines.append(curr)
            matrix_index = end_index
            
    def num_points(self, what="landmarks"):
        if what == "landmarks":
            return (len(self.analyzed_landmarks) * 3)
        elif what == "lines":
            total = 0
            for line in self.analyzed_lines:
                total += len(line.as_list)
            return total
                       
class Datapoint:
    def __init__(self, label):
        self.label = label
        self.as_list = []
        
    def add_point(self, point):
        for item in point:    
            self.as_list = self.as_list + [float32(item),]
            
    def points_as_string(   self, 
                            missing_data    =   "9999", 
                            no_per_line     =   3, 
                            linefeed        =   "unix"):
        as_string = ''
        index = 0
        if linefeed=="windows":
            eol = '\r\n'
        else:
            eol = '\n'
        while index < len(self.as_list):
            out_value = self.as_list[index]
            if fpconst.isNaN(out_value):
                out_value = missing_data
            else:
                out_value = "%3f" % out_value
            if ((index+1) % no_per_line) != 0:
                as_string += out_value + (' ' * (15-len(out_value)))
            else:
                as_string += out_value + eol
            index += 1
        if len(self.as_list) > 3:
            as_string += eol
        return as_string

class RegList:
    def __init__(self):
        self.as_list = None
        self.labels = []
        
    def add_landmark(self, landmark):
        self.labels.append(landmark.label)
        if not self.as_list:
            self.as_list = landmark.as_list
        else:
            self.as_list = self.as_list + landmark.as_list
            
    def as_matrix(self):
        num_points = len(self.as_list)/3
        m = matrix(self.as_list)
        m.resize(num_points,3)
        return m

class Prn:
    def __init__(self):
        self.view1 = None
        self.view2 = None
        self.last_view = None
        self.curr_view = None
        self.curr_datapoint = None
        
    def read(self, filename):
        self.basename = os.path.basename(filename).split('.')[0]
        infile = open(filename)
        for line in infile:
            if re.match("^#", line) or re.match("^\s", line):
                continue
            line = line.rstrip()
            tokens = re.split('\s*', line)
        
            if (len(tokens) > 4) and tokens[4]:
                if not self.view1:
                    self.view1 = View(tokens[4])
                    self.curr_view = self.view1
                elif not self.view2:
                    self.view2 = View(tokens[4])
                    self.curr_view = self.view2
                else:
                    raise Error
                    
            if (len(tokens) > 3) and tokens[3]:
                if self.curr_datapoint and self.last_view:
                    self.last_view.add_datapoint(self.curr_datapoint)
                self.curr_datapoint = Datapoint(tokens[3])
            
            if tokens[0] == "9999":
                self.curr_datapoint.add_point(["NaN", "NaN", "NaN"])
            else:
                self.curr_datapoint.add_point(tokens[0:3])
                
            self.last_view = self.curr_view
        self.last_view.add_datapoint(self.curr_datapoint)
        infile.close()

    def analyze(self):
        self.process_views()
        # get registration matrices
        R1 = self.view1.reg_matrix()
        R2 = self.view2.reg_matrix()
        
        (rmsd, q, Q) = suppos(transpose(R1), transpose(R2))
        
        V1_landmarks = self.view1.landmarks_matrix()
        V2_landmarks = self.view2.landmarks_matrix()
        V1_lines = self.view1.lines_matrix()
        V2_lines = self.view2.lines_matrix()
        
        V2_landmarks_aligned = Q * transpose(V2_landmarks) + q
        V2_lines_aligned = Q * transpose(V2_lines) + q
        
        self.view1.update_landmarks(V1_landmarks)
        self.view1.update_lines(V1_lines)
        self.view2.update_landmarks(transpose(V2_landmarks_aligned))
        self.view2.update_lines(transpose(V2_lines_aligned))
    
    def process_views(self):
        # find registration points
        reg_point_labels = []
        view1_labels = self.view1.labels()
        view2_labels = self.view2.labels()
        for label in view1_labels:
            if label in view2_labels:
                reg_point_labels.append(label)
        self.view1.set_reg_points(reg_point_labels)
        self.view2.set_reg_points(reg_point_labels)
        # split landmarks and lines in views
        self.view1.split_lines_and_landmarks()
        self.view2.split_lines_and_landmarks()
        
    def make_individual(self):
        landmarks = self.view1.analyzed_landmarks
        landmarks += self.view2.analyzed_landmarks
        lines = self.view1.analyzed_lines 
        lines += self.view2.analyzed_lines
        options = { "label"     :   self.basename,
                    "landmarks" :   landmarks,
                    "lines"     :   lines,
                    "dimensions":   3 }
        return Individual(options)
        
            
class Individual:
    def __init__(self, options):
        self.label = options["label"]
        self.landmarks = options["landmarks"] # list of Datapoints
        self.lines = options["lines"] # list of Datapoints
        if options.has_key("dimensions"):
            self.dimensions = options["dimensions"]
        else:
            self.dimensions = 3
            
    def num_points(self, including_lines=False):
        total = (len(self.landmarks) * self.dimensions)
        if including_lines:
            for line in self.lines:
                total += len(line.as_list)
        return total
            
class Collection:
    def __init__(self):
        self.individuals = []
        
    def add_individual(self, individual):
        self.individuals.append(individual)
        
class Writer:
        
    def write(self, collection, options):
        pass
        
    def options(self):
        return []
    
class GRFNDWriter(Writer):
    def __init__(self):
        self.identifier = 'GRFND'
        pattern = '^(?:GRFND,)(.*)'
        self.regex = re.compile(pattern)
    
    def write(self, collection, options):
        options = [ self.regex.match(x).group(1) 
                    for x in options 
                    if x.startswith(self.identifier)]
        if "landmarks by individual" in options:
            self.write_landmarks(collection)
        if "landmarks and lines by individual" in options:
            self.write_landmarks_and_lines(collection)
        if "all individuals combined (landmarks only)" in options:
            self.write_combined(collection)
                    
    def options(self):
        return ["landmarks by individual", 
                "landmarks and lines by individual", 
                "all individuals combined (landmarks only)"]
                
    def write_landmarks(self, collection):
        if __name__ == "__main__":
            directory = os.path.curdir
        else:
            dt = "Save individual GRFND landmark files where?"
            directory = tkFileDialog.askdirectory(title=dt)
        for individual in collection.individuals:
            outname = os.path.join(directory, individual.label + '.dt1')
            outfile = open(outname, 'w')
        
            # set up file header
            header = "1 1 %s 1 9999 DIM=%s\n" % ( individual.num_points(), 
                                                  individual.dimensions   )
            outfile.write(header)
        
            # write out data
            for landmark in individual.landmarks:
                outfile.write(landmark.points_as_string())
            outfile.close()
            
    def write_landmarks_and_lines(self, collection):
        if __name__ == "__main__":
            directory = os.path.curdir
        else:
            dt = "Save individual GRFND landmark and line files where?"
            directory = tkFileDialog.askdirectory(title=dt)
        for individual in collection.individuals:
            outname = os.path.join(directory, individual.label + '.dt2')
            outfile = open(outname, 'w')
        
            # set up file header
            num_points = individual.num_points(including_lines=True)
            header = "1 1 %s 1 9999 DIM=%s\n" % ( num_points,
                                                  individual.dimensions )
            outfile.write(header)
        
            # write out data
            for landmark in individual.landmarks:
                outfile.write(landmark.points_as_string())
            outfile.write('\n')
            for line in individual.lines:
                outfile.write(line.points_as_string())
            outfile.close()
            
    def write_combined(self, collection):
        num_points = None
        dimensions = None
        num_individuals = len(collection.individuals)
        labels = ''
        points = ''
        for individual in collection.individuals:
            points += "\n"
            if not num_points:
                num_points = individual.num_points()
            if not dimensions:
                dimensions = individual.dimensions
            for landmark in individual.landmarks:
                points += landmark.points_as_string()
            labels += individual.label + '\n'
        header = "1 %sL %s 1 9999 DIM=%s\n" % ( num_individuals, 
                                                num_points, 
                                                dimensions  )
        if __name__ == "__main__":
            outname = os.path.join(os.path.curdir, 'combined.dt0')
        else:
            dt = "Save combined GRFND landmark file as?"
            df = "combined_grfnd.prn"
            outname = tkFileDialog.asksaveasfilename( title=dt,
                                                      initialfile=df,
                                                      filetypes=SAVE_FILE_TYPES)
        outfile = open(outname, 'w')
        outfile.write(header)
        outfile.write(labels)
        outfile.write(points)
        outfile.close()
    
class MorphologikaWriter(Writer):
    def __init__(self):
        self.identifier = 'Morphologika'
        pattern = '^(?:Morphologika,)(.*)'
        self.regex = re.compile(pattern)
        
    def write(self, collection, options):
        options = [ self.regex.match(x).group(1) 
                    for x in options 
                    if x.startswith(self.identifier) ]
        if "all individuals combined (landmarks only)" in options:
            self.write_combined(collection)
            
    def options(self):
        return ["all individuals combined (landmarks only)"]
        
    def write_combined(self, collection):
        num_landmarks = None
        dimensions = None
        num_individuals = len(collection.individuals)
        labels = ''
        points = ''
        for individual in collection.individuals:
            points += "'%s\r\n" % individual.label
            if not num_landmarks:
                num_landmarks = len(individual.landmarks)
            if not dimensions:
                dimensions = individual.dimensions
            for landmark in individual.landmarks:
                points += landmark.points_as_string(linefeed="windows")
            labels += individual.label + '\r\n'
        if __name__ == "__main__":
            outname = os.path.join(os.path.curdir, 'combined.mka')
        else:
            dt = "Save combined Morphologika landmark file as?"
            df = "combined_morphologika.prn"
            outname = tkFileDialog.asksaveasfilename( title=dt,
                                                      initialfile=df,
                                                      filetypes=SAVE_FILE_TYPES)
        outfile = open(outname, 'w')
        outfile.write("[individuals]\r\n%s\r\n" % num_individuals)
        outfile.write("[landmarks]\r\n%s\r\n" % num_landmarks)
        outfile.write("[dimensions]\r\n%s\r\n" % dimensions)
        outfile.write("[names]\r\n")
        outfile.write(labels)
        outfile.write("[rawpoints]\r\n")
        outfile.write(points)
        outfile.close()

def suppos(X, Z):
    
    (m,n) = X.shape
    
    meanX = mean(X, 1)
    meanZ = mean(Z, 1)
     
    X = X - meanX
    Z = Z - meanZ

    ZT = transpose(Z)
    
    A = X * ZT
    
    (U, s, V) = linalg.svd(A)  
   
    VT = transpose(V)

    Q = U * VT

    q = meanX - Q * meanZ
    
    Rmsd = X - Q * Z
    rmsd = linalg.norm(Rmsd)/sqrt(n)
    
    return (rmsd,q,Q)
    
def dvlr(filenames, output_formats):
    failed_to_process = []
    processed = []
    c = Collection()
    for filename in filenames:
        try:
            p = Prn()
            p.read(filename)
            p.analyze()
            c.add_individual(p.make_individual()) 
            processed.append(filename)           
        except:
            failed_to_process.append(filename)
    
    available_writers = []
    for item in globals().keys():
        if item.endswith('Writer') and item != 'Writer':
            available_writers.append(globals()[item]())
    for writer in available_writers:
        writer.write(c, output_formats)
    return (processed, failed_to_process)
           
def main(argv=None):
    if argv is None:
        argv = sys.argv
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
    # process arguments
    dvlr(args, ["Morpheus,landmarks by individual"])
    
if __name__ == "__main__":
    main()
    
            
