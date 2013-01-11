

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
    