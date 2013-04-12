###  Author: Ben Burry <ben@burry.name>
###
###  A logster parser that can be used to count the number of log entries
###   matching a supplied regular expression, and output the metrics
###   using an optional template.
###
###  For example, to reproduce the behaviour of SampleLogster one would this regex/template combination:
###  sudo ./logster --output=stdout RegexCountLogster /var/log/httpd/access_log --parser-options '-r .*HTTP/1.\d\"\s(?P<status_code>\d)\d{2}\s.* -t http_<status_code>xx'
###
###

import re
import optparse
from collections import defaultdict

from logster.logster_helper import MetricObject, LogsterParser
from logsterlogster_helper import LogsterParsingException


class RegexCountLogster(LogsterParser):

    PLACEHOLDER_REG = re.compile(r'<[^>]+>')

    def __init__(self, option_string=None):
        if option_string:
            options = option_string.split(' ')
        else:
            options = []

        optparser = optparse.OptionParser()
        optparser.add_option('--regex',
                             '-r',
                             dest='regex',
                             help='''Regular expression for matching lines.
                                  Should include named placeholders for values to use in metric name.''')
        optparser.add_option('--metric-template',
                             '-t',
                             dest='template',
                             default=None,
                             help='''Template to use in building the metric name from named placeholders.
                                  <placeholder> entries in template are replaced by corresponding named placeholder value from regex.''')

        opts, args = optparser.parse_args(args=options)

        self.reg = re.compile(opts.regex)
        self.template = opts.template
        if self.template is None:
            self.template = '.'.join(RegexCountLogster.PLACEHOLDER_REG.findall(opts.regex))
        self.metrics = defaultdict(float)

    def parse_line(self, line):
        try:
            regMatch = self.reg.match(line)

            if regMatch:
                linebits = regMatch.groupdict()
                metric = RegexCountLogster.PLACEHOLDER_REG.sub(lambda x: linebits.get(x.group()[1:-1], ''), self.template)
                self.metrics[metric] += 1.0

        except Exception, e:
            raise LogsterParsingException, "regmatch or contents failed with %s" % e

    def get_state(self, duration):
        self.duration = float(duration)

        return [MetricObject(metric, count / self.duration) for metric, count in self.metrics.iteritems()]
