#!/usr/bin/python

from datetime import datetime
from subprocess import Popen, PIPE
import argparse
import boto3
import conf.defaults as defaults
import json
import numpy as np


S3 = boto3.resource('s3')
SES = boto3.client('ses', region_name='eu-west-1')
EMAIL_SUBJECT = "AWS EC2 Network Performance Benchmark Daily Report"
CHARSET = 'UTF-8'
HOURLY_RESULTS = []  # Mbps
LAST_DAY = -1


def set_email_subject():
    global EMAIL_SUBJECT
    aws_availability_zone = '[%s]' % Popen('ec2-metadata -z | sed \'s/.*\\: //\'', shell=True, stdout=PIPE).communicate()[0].decode('utf-8')

    if aws_availability_zone != '[]':
        EMAIL_SUBJECT = '%s %s' % (aws_availability_zone, EMAIL_SUBJECT)


def send_email_notif(data, sender, recipients):
    try:
        response = SES.send_email(
            Destination={
                'ToAddresses': recipients
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': str(data)
                    }
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': EMAIL_SUBJECT
                }
            },
            Source=sender
        )
    except Exception as e:
        print(e)


def upload_results(data):
    filename = str(datetime.now()) + '.json'
    o = S3.Object('perf-var', filename)
    o.put(Body=json.dumps(data))


def run_iperf(server_ip, duration, interval, num_streams, sender, recipients):
    global HOURLY_RESULTS
    try:
        cmd_res = Popen(['iperf3', '-c', server_ip, '--time', str(duration), '--interval', str(interval), '--json', '-P', str(num_streams)], stdout=PIPE, stderr=PIPE).communicate()[0].decode('utf-8')
        result = json.loads(cmd_res)

        upload_results(result)

        for interval in result['intervals']:
            HOURLY_RESULTS.append(interval['sum']['bits_per_second'] / (1024 * 1024))

    except Exception as e:
        data = {'Error': e}
        send_email_notif(data, sender, recipients)


def generate_metrics():
    global HOURLY_RESULTS
    quartiles = np.percentile(HOURLY_RESULTS, [25, 50, 75])
    data_min, data_max = min(HOURLY_RESULTS), max(HOURLY_RESULTS)
    mean = np.mean(HOURLY_RESULTS)

    result = {
        'Mean': mean,
        'Max': data_max,
        'Q3': quartiles[2],
        'Median': quartiles[1],
        'Q1': quartiles[0],
        'Min': data_min
    }

    return result


def turnover_iperf(server_ip, duration, interval, num_streams, sender, recipients):
    global LAST_DAY, HOURLY_RESULTS
    run_iperf(server_ip, duration, interval, num_streams, sender, recipients)
    day = datetime.now().day

    if day != LAST_DAY:
        LAST_DAY = day
        data = generate_metrics()
        HOURLY_RESULTS.clear()
        send_email_notif(data, sender, recipients)


def main():
    global LAST_DAY, HOURLY_RESULTS
    parser = argparse.ArgumentParser(description="Network performance benchmark")
    parser.add_argument("--server", action="store_true", dest="is_server",
                        help="Run as server")
    parser.add_argument("--client", metavar="", dest="server_ip", type=str,
                        action="store", default=defaults.server_ip,
                        help="Run as client and connect to provided server")
    parser.add_argument("-d", "--duration", metavar="", dest="duration", type=int,
                        action="store", default=defaults.duration,
                        help="Duration per turnover")
    parser.add_argument("-i", "--interval", metavar="", dest="interval", type=int,
                        action="store", default=defaults.interval,
                        help="Report interval")
    parser.add_argument("-n", "--num-streams", metavar="", dest="num_streams", type=int,
                        action="store", default=defaults.num_streams,
                        help="Parallel streams")
    parser.add_argument("--email-sender", metavar="", dest="email_sender",
                        action="store", default=defaults.email_sender,
                        help="E-mail sender")
    parser.add_argument("--email-recipients", metavar="", dest="email_recipients",
                        action="store", default=defaults.email_recipients,
                        help="Comma separated e-mail recipient addresses")

    args = parser.parse_args()
    email_recipients = args.email_recipients.split(',')
    LAST_DAY = datetime.now().day

    if not args.is_server:
        while True:
            turnover_iperf(args.server_ip, args.duration, args.interval, args.num_streams, args.email_sender, email_recipients)
    else:
        while True:
            cmd_res = Popen(['iperf3', '-s'], stdout=PIPE, stderr=PIPE).communicate()[0]


if __name__ == "__main__":
    main()

