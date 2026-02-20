import sys, os, traceback

def debug_exit(code=0):
    print(f"SYS.EXIT CALLED WITH CODE {code}!!!")
    traceback.print_stack()
    os._exit(code)

sys.exit = debug_exit

try:
    import main
    print("IMPORT FINISHED SUCCESSFULLY without exiting!")
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()

