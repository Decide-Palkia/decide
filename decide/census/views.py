from django.db.utils import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.core import serializers
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework.status import (
    HTTP_201_CREATED as ST_201,
    HTTP_204_NO_CONTENT as ST_204,
    HTTP_400_BAD_REQUEST as ST_400,
    HTTP_401_UNAUTHORIZED as ST_401,
    HTTP_409_CONFLICT as ST_409
)

from base.perms import UserIsStaff
from census.models import Census
from django.contrib.auth.models import User
from voting.models import Voting
import django_excel as excel
from django.http import FileResponse
import io
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table, TableStyle)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors


class CensusCreate(generics.ListCreateAPIView):
    permission_classes = (UserIsStaff,)

    def create(self, request, *args, **kwargs):
        voting_id = request.data.get('voting_id')
        voters = request.data.get('voters')
        try:
            for voter in voters:
                census = Census(voting_id=voting_id, voter_id=voter)
                census.save()
        except IntegrityError:
            return Response('Error try to create census', status=ST_409)
        return Response('Census created', status=ST_201)

    def list(self, request, *args, **kwargs):
        voting_id = request.GET.get('voting_id')
        voters = Census.objects.filter(voting_id=voting_id).values_list('voter_id', flat=True)
        return Response({'voters': voters})


class CensusDetail(generics.RetrieveDestroyAPIView):

    def destroy(self, request, voting_id, *args, **kwargs):
        voters = request.data.get('voters')
        census = Census.objects.filter(voting_id=voting_id, voter_id__in=voters)
        census.delete()
        return Response('Voters deleted from census', status=ST_204)

    def retrieve(self, request, voting_id, *args, **kwargs):
        voter = request.GET.get('voter_id')
        try:
            Census.objects.get(voting_id=voting_id, voter_id=voter)
        except ObjectDoesNotExist:
            return Response('Invalid voter', status=ST_401)
        return Response('Valid voter')

@staff_member_required
def listaVotantes(request, voting_id):
    census = list(Census.objects.filter(voting_id=voting_id))
    datos = []
    for c in census:
        user = list(User.objects.filter(pk=c.voter_id))[0]
        votacion = list(Voting.objects.filter(pk=c.voting_id))[0]
        tupla = (user, votacion, c.pk)
        datos.append(tupla)
    return render(request, 'tabla.html', {'datos': datos, 'voting_id': voting_id, 'STATIC_URL': settings.STATIC_URL})

@staff_member_required
def listaCensos(request):
    census = list(Census.objects.all())
    datos = []
    for c in census:
        user = list(User.objects.filter(pk=c.voter_id))[0]
        votacion = list(Voting.objects.filter(pk=c.voting_id))[0]
        tupla = (user, votacion, c.pk)
        datos.append(tupla)

    dist_pk = Voting.objects.values('pk').distinct()
    dist_name = Voting.objects.values('name').distinct()

    dist = []
    for counter, pk in enumerate(dist_pk):
        tupla = (pk, dist_name[counter])
        dist.append(tupla)

    return render(request, 'tabla.html', {'datos': datos, 'dist': dist, 'STATIC_URL': settings.STATIC_URL})

@staff_member_required
def export_csv(request):
    voting_id = request.GET.get('voting_id')
    if voting_id is '':
        voting_id = -1

    if voting_id is not None:
        census = list(Census.objects.filter(voting_id=voting_id))
        datos = []
        for c in census:
            user = list(User.objects.filter(pk=c.voter_id))[0]
            votacion = list(Voting.objects.filter(pk=c.voting_id))[0]
            tupla = (user, votacion)
            datos.append(tupla)
        sheet = ExportToCsv(datos)
    else:
        census = list(Census.objects.all())
        datos = []
        for c in census:
            user = list(User.objects.filter(pk=c.voter_id))[0]
            votacion = list(Voting.objects.filter(pk=c.voting_id))[0]
            tupla = (user, votacion)
            datos.append(tupla)
        sheet = ExportToCsv(datos)
    return excel.make_response(sheet, "csv", file_name="census_data.csv")

@staff_member_required
def ExportToCsv(datos):
    export = []
    export.append([
        'Nombre',
        'Apellido',
        'Edad',
        'Sexo',
        'Municipio',
        'Votación', ])

    for dato in datos:
        if hasattr(dato[0], 'perfil'):
            export.append(
                [dato[0].first_name, dato[0].last_name, dato[0].perfil.edad, dato[0].perfil.sexo,
                 dato[0].perfil.municipio,
                 str("/census/web/" + str(dato[1].pk))])

    sheet = excel.pe.Sheet(export)

    return sheet

@staff_member_required
def export_excel(request):
    voting_id = request.GET.get('voting_id')
    if voting_id is '':
        voting_id = -1

    census = list(Census.objects.filter(voting_id=voting_id))

    users = []
    for cen in census:
        user = list(User.objects.filter(pk=cen.voter_id))[0]
        users.append(user.username)

    template = export_to_xlsx(users)

    voting = Voting.objects.filter(pk=voting_id)

    return excel.make_response(template, "xlsx", file_name=voting.name + ".xlsx")


@staff_member_required
def export_to_xlsx(users):
    export = [[
        'Nombre',
        'Apellido',
        'Edad',
        'Sexo',
        'Municipio']]

    for u in users:
        if hasattr(u, 'perfil'):
            export.append([u.first_name, u.last_name, u.perfil.edad, u.perfil.sexo, u.perfil.municipio])

    template = excel.pe.Sheet(export)

    return template

@staff_member_required
def addCensus(request):
    id = request.POST.get("id")
    votacion_id = request.POST.get("voting_id")
    votacion = get_object_or_404(Voting, pk=votacion_id)
    tipo = request.POST.get("tipo")
    if tipo == "usuario":
        usuario = get_object_or_404(User, pk=id)
        try:
            Census.objects.create(voter_id=usuario.pk, voting_id=votacion.pk)
        except:
            pass

    elif tipo == "votacion":
        votacion2 = get_object_or_404(Voting, pk=id)
        census = list(Census.objects.filter(voting_id=votacion2.pk))
        for c in census:
            try:
                Census.objects.create(voting_id=votacion.pk, voter_id=c.voter_id)
            except:
                pass

    usuarios = User.objects.all()
    votaciones = Voting.objects.all().exclude(pk=votacion.pk)
    census = list(Census.objects.filter(voting_id=votacion.pk))
    datos = []
    for c in census:
        u = list(User.objects.filter(pk=c.voter_id))[0]
        v = list(Voting.objects.filter(pk=c.voting_id))[0]
        tupla = (u, v)
        datos.append(tupla)

    return render(request, 'add.html',
                  {'datos': datos, 'usuarios': usuarios, 'votaciones': votaciones, 'vot_id': votacion_id,
                   'STATIC_URL': settings.STATIC_URL})

@staff_member_required
def exportToPdf(request):
    if request.GET.get('voting_id') is not None:
        voting_id = request.GET.get('voting_id')
        census = list(Census.objects.filter(voting_id=voting_id))
        datos = []
        for c in census:
            user = list(User.objects.filter(pk=c.voter_id))[0]
            votacion = list(Voting.objects.filter(pk=c.voting_id))[0]
            tupla = (user, votacion)
            datos.append(tupla)
        buffer = generatePdf(datos)
    else:
        census = list(Census.objects.all())
        datos = []
        for c in census:
            user = list(User.objects.filter(pk=c.voter_id))[0]
            votacion = list(Voting.objects.filter(pk=c.voting_id))[0]
            tupla = (user, votacion)
            datos.append(tupla)
        buffer = generatePdf(datos)
    buffer.seek(0)
    response = FileResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="census_data.pdf"'
    return response

@staff_member_required
def generatePdf(datos):
    buff = io.BytesIO()
    doc = SimpleDocTemplate(buff, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=18)
    tabla = []
    styles = getSampleStyleSheet()
    header = Paragraph("Datos del censo", styles['Heading1'])
    tabla.append(header)

    headings = ('Nombre', 'Apellido', 'Edad', 'Sexo', 'Municipio', 'Votación')
    censo = []
    for d in datos:
        if hasattr(d[0], 'perfil'):
            censo.append(
                [d[0].first_name, d[0].last_name, d[0].perfil.edad, d[0].perfil.sexo, d[0].perfil.municipio,
                 str("/census/web/" + str(d[1].pk))])

    t = Table([headings] + censo, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
    ]))
    tabla.append(t)
    doc.build(tabla)

    buff.seek(0)
    response = FileResponse(buff, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="census_data.pdf"'
    return buff

@staff_member_required
def eliminaCenso(request, census_id):
    census = get_object_or_404(Census, pk=census_id)
    census.delete()
    return listaCensos(request)
