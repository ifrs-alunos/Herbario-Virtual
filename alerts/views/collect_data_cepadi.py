import csv
import ftplib

from django.http import HttpResponse


def collect_data_cepadi(request):
    server = ftplib.FTP()
    server.connect("cepadi.vacaria.ifrs.edu.br")
    server.cwd("/labfito/dados")
    files = server.nlst()
    last_file = files[-1]
    server.retrbinary(f"RETR {last_file}", open(f"{last_file}", "wb").write)
    with open(f"{last_file}", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            print(row)

    server.quit()
    return HttpResponse("Dados cepadi")
