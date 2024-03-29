import lib.watch
import sys

if __name__ == '__main__':
    if len(sys.argv) > 2:
        if sys.argv[1] == 'eink':
            import lib.render_eink
            lib.watch.start(sys.argv[2], lib.render_eink.render)
        else:
            import lib.render_cli
            lib.watch.start(sys.argv[2], lib.render_cli.render)
    print("Invalid usage")
    print("python ./main.py [eink|*] <datafile-path>")
    exit(1)
