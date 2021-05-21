import os, argparse, json, requests
from icmplib import ping
from pyzabbix import ZabbixMetric, ZabbixSender

urlgetip = 'https://ifconfig.me'
ZabbixAddress = os.getenv('ZBXADDRESS', '127.0.0.1')

parser = argparse.ArgumentParser(description="Sophos Gateway Monitoring by CDR Tecnologia")
parser.add_argument(
    '-d',
    '--discovery',
    help='Run Gateway Discovery',
    action="store_true"
)
parser.add_argument(
    '-s',
    '--send',
    help="Send Collected Info",
    action="store_true"
)
parser.add_argument(
    '-f',
    '--file',
    help='Gateways names and address to test',
    default='dest.txt'
)
parser.add_argument(
    '-z',
    '--zabbixhostname',
    help="Hostname in Zabbix Server",
    default="Zabbix server"
)
args = parser.parse_args()

if args.discovery:
    destlist = []
    zmetric = []
    with open(args.file) as file:
        for line in file:
            fileparse = line.strip().split(";")
            destdict = {"{#DESTNAME}": fileparse[0]}
            destlist.append(destdict)
    datadiscovery = json.dumps(
        {'data': destlist})
    metric = ZabbixMetric('Zabbix server', 'destination.discovery', datadiscovery)
    zmetric.append(metric)
    zbxs = ZabbixSender(ZabbixAddress)
    zbxs.send(zmetric)

if args.send:
    zmetric = []
    scrip = requests.get(urlgetip)
    zmetric.append(ZabbixMetric(args.zabbixhostname, 'gateway.default', scrip.text))
    with open(args.file) as file:
        for line in file:
            fileparse = line.strip().split(";")
            destname = fileparse[0]
            destaddr = fileparse[1]
            pingresult = ping(destaddr, count=10, interval=0.3)
            zmetric.append(ZabbixMetric(args.zabbixhostname, f'gateway[delay,{destname}]', pingresult.avg_rtt))
            zmetric.append(ZabbixMetric(args.zabbixhostname, f'gateway[loss,{destname}]', pingresult.packet_loss))
            zmetric.append(ZabbixMetric(args.zabbixhostname, f'gateway[monitorip,{destname}]', pingresult.address))
            if pingresult.is_alive:
                zmetric.append(ZabbixMetric(args.zabbixhostname, f'gateway[status,{destname}]', 1))
            else:
                zmetric.append(ZabbixMetric(args.zabbixhostname, f'gateway[status,{destname}]', 0))
    zbxs = ZabbixSender(ZabbixAddress)
    zbxs.send(zmetric)
