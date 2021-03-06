# coding: utf-8
import os
import os.path
import sys
import optparse

import acmd
import acmd.tools

USAGE = """acmd [options] <tool> <args>
    Run 'acmd help' for list of available tools"""

parser = optparse.OptionParser(USAGE)
parser.add_option("-s", "--server", dest="server",
                  help="server name", metavar="<name>")
parser.add_option("-v", "--verbose",
                  action="store_const", const=True, dest="verbose",
                  help="verbose logging useful for debugging")
parser.add_option("-V", "--version",
                  action="store_const", const=True, dest="show_version",
                  help="Show package version")


def load_projects(projects):
    """ Load any user specified tools directories.
        Expecting dict of {<prefix>: <path>} """
    ret = {}
    for name, path in projects.items():
        acmd.log("Loading project {}".format(name))
        path = os.path.expanduser(path)
        sys.path.insert(1, path)
        init_file = os.path.join(path, '__init__.py')
        acmd.tool_repo.set_current_project(name)
        acmd.import_tools(init_file)
        ret[name] = path
    return ret


def run(options, config, args, cmdargs):
    tool_name, args = args[1], []
    server = config.get_server(options.server)
    if server is None:
        sys.stderr.write("error: server '{srv}' not found.\n".format(srv=options.server))
        return acmd.USER_ERROR
    acmd.log("Using server {}".format(server))

    _tool = acmd.tool_repo.get_tool(tool_name)
    if _tool is None:
        sys.stderr.write("error: tool '{cmd}' not found.\n".format(cmd=tool_name))
        return acmd.USER_ERROR
    else:
        return _tool.execute(server, cmdargs)


def split_argv(argv):
    """ Split argument list into system arguments before the tool
        and tool arguments afterwards.
        ['foo', 'bar', 'inspect', 'bink', 'bonk']
            => (['foo', 'bar', 'inspect'], ['inspect', 'bink', 'bonk'])"""
    acmd.log("Splitting {}".format(argv))
    for i, arg in enumerate(argv):
        acmd.log("Checking for {}".format(arg))
        if acmd.tool_repo.has_tool(arg):
            left = argv[0:i + 1]
            right = argv[i:]
            acmd.log("Splitting args in {} and {}".format(left, right))
            return left, right
    return argv, []


def main(argv):
    rcfilename = acmd.get_rcfilename()
    if not os.path.isfile(rcfilename):
        acmd.setup_rcfile(rcfilename)
    config = acmd.read_config(rcfilename)
    load_projects(config.projects)

    acmd.tools.init_default_tools()

    sysargs, cmdargs = split_argv(argv)
    (options, args) = parser.parse_args(sysargs)
    acmd.init_log(options.verbose)

    if options.show_version:
        sys.stdout.write("{}\n".format(acmd.__version__))
        sys.exit(0)
    if len(args) <= 1:
        parser.print_help(file=sys.stderr)
        sys.exit(acmd.USER_ERROR)

    status = run(options, config, args, cmdargs)
    sys.exit(status)
