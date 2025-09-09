import moduleRules
from configMod import *


class srcDst:
    def readArgs(self):
        import argparse

        parser = argparse.ArgumentParser(
            description="Improving command line call", allow_abbrev=True
        )
        parser.add_argument(
            "--timeSlots",
            "-t",
            default=50,  # 50 minutes
            help=("How many time slots we will have for publishing " f"(in minutes)"),
        )
        parser.add_argument(
            "checkBlog",
            default="",
            metavar="Blog",
            type=str,
            nargs="?",
            help="you can select just a blog",
        )
        parser.add_argument(
            "--simmulate",
            "-s",
            default=False,
            action="store_true",
            help="simulate which posts would be added",
        )
        parser.add_argument(
            "--noWait",
            "-n",
            default=False,
            action="store_true",
            help="no wait for time restrictions",
        )
        args = parser.parse_args()

        return args


def main():
    logging.basicConfig(
        filename=LOGDIR + "/rssSocial.log",
        level=logging.INFO,
        format="%(asctime)s [%(filename).12s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    msgLog = "Launched at %s" % time.asctime()
    logMsg(msgLog, 1, 2)

    rules = moduleRules.moduleRules()
    srcs, dsts, ruls, impRuls = rules.checkRules()

    local = srcDst()
    args = local.readArgs()

    rules.executeRules(args)

    return
