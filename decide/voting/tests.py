import random
import itertools
import re
import os
import markdown
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from django.test import Client
from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Voting, Candidate, CandidatesGroup
from voting.views import handle_uploaded_file, copy_voting
import unittest
from selenium import webdriver
from django.urls import reverse

class VotingTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def create_voting(self):       
        cg = CandidatesGroup(name='PP')  
        groups = []
        groups.append(cg)     
        cg.save()       
        for i in range(5):           
            candidate = Candidate(name='Juan', type='PRESIDENCIA', born_area='AB',current_area='AB', primaries=True, sex='HOMBRE', candidatesGroup=cg)           
            candidate.save()       
            v = Voting(name='test voting', desc='desc')     
            v.save()       
            v.candidatures.set(groups)  
            a, _ = Auth.objects.get_or_create(url=settings.BASEURL,defaults={'me': True, 'name': 'test auth'})       
            a.save()       
            v.auths.add(a)       
        return v

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voting_gobern(self):
        v = Voting(name="Votación Gobierno 2020")
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v


    def create_voters(self, v):
        for i in range(100):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def create_candidateGroup(self):
        v = CandidatesGroup(name='test candidatesGroup')
        v.save()
        return v

    def create_candidate(self):
        c = Candidate(name='candidate', type='PRESIDENCIA', born_area='SE', current_area='SE', primaries=False, sex='HOMBRE', candidatesGroup=self.create_candidateGroup())
        c.save()
        return c

    def test_create_candidateGroup(self):
        self.login()
        v = self.create_candidateGroup()
        self.assertIsNotNone(v, 'Creating CandidatesGroup')

    def test_create_candidate(self):
        self.login()
        c = self.create_candidate()
        self.assertIsNotNone(c, 'Creating Candidate')

#TEST DAVID
    def csv_validation_genres_test(self):
        num_candidatos_inicial = len(Candidate.objects.all())
        path = str(os.getcwd()) + "/voting/files/candidatos-test-genero.csv"
        with open(path, 'r') as archivo:
            csv = archivo.read() 
        c = Client()
        data = {'param': csv, 'candidature_name': "prueba"}
        request = c.post('/voting/validate/', data, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        http_content = str(request.content.decode('utf-8'))
        count_errors = http_content.count('La candidatura prueba no cumple un balance 60-40 entre hombres y mujeres')
        num_candidatos_final = len(Candidate.objects.all())
        self.assertTrue(count_errors == 1)
        self.assertTrue(num_candidatos_inicial == num_candidatos_final)

    def csv_validation_maximum_candidates_test(self):
        num_candidatos_inicial = len(Candidate.objects.all())
        path = str(os.getcwd()) + "/voting/files/candidatos-test-maximo.csv"
        with open(path, 'r') as archivo:
            csv = archivo.read() 
        c = Client()
        data = {'param': csv, 'candidature_name': "prueba"}
        request = c.post('/voting/validate/', data, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        http_content = str(request.content.decode('utf-8'))
        count_errors = http_content.count('La candidatura prueba supera el máximo de candidatos permitidos (350)')
        num_candidatos_final = len(Candidate.objects.all())
        self.assertTrue(count_errors == 1 and num_candidatos_inicial == num_candidatos_final)

    def csv_validation_presidents_test(self):
        num_candidatos_inicial = len(Candidate.objects.all())
        path = str(os.getcwd()) + "/voting/files/candidatos-test-presidents.csv"
        with open(path, 'r') as archivo:
            csv = archivo.read() 
        c = Client()
        data = {'param': csv, 'candidature_name': "prueba"}
        request = c.post('/voting/validate/', data, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        http_content = str(request.content.decode('utf-8'))
        count_errors = http_content.count('La candidatura prueba tiene más de un candidato a presidente')
        num_candidatos_final = len(Candidate.objects.all())
        self.assertTrue(count_errors == 1 and num_candidatos_inicial == num_candidatos_final)

    def csv_correct_test(self):
        num_candidatos_inicial = len(Candidate.objects.all())
        path = str(os.getcwd()) + "/voting/files/podemos.csv"
        with open(path, 'r') as archivo:
            csv = archivo.read() 
        c = Client()
        data = {'param': csv, 'candidature_name': "prueba"}
        request = c.post('/voting/validate/', data, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        http_content = str(request.content.decode('utf-8'))
        count_errors = http_content.count('La candidatura prueba tiene los siguientes errores:')
        num_candidatos_final = len(Candidate.objects.all())
        self.assertTrue(count_errors == 0 and (num_candidatos_inicial + 105) == num_candidatos_final)
    
    def voting_correct_copy_test(self):
        inicial_voting = Voting(name="votacion creada", desc="nueva votacion")
        candidature = CandidatesGroup(name="candidatura1")
        auth = Auth(name="auth1", url="http://auth1.com")
        candidature.save()
        auth.save()
        candidatures = []
        auths = []
        candidatures.append(candidature)
        auths.append(auth)
        inicial_voting.save()
        inicial_voting.candidatures.set(candidatures)
        inicial_voting.auths.set(auths)
        inicial_voting.save()
        num_voting_inicial = len(Voting.objects.all())
        voting_id = Voting.objects.get(name="votacion creada").id
        c = Client()
        response = c.get(reverse('copy_voting', kwargs={'voting_id':voting_id}), {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        response.user = self.login()
        num_voting_final = len(Voting.objects.all())
        create_votings = Voting.objects.filter(name="votacion creada", desc="nueva votacion", candidatures__in=candidatures, auths__in=auths)
        self.assertTrue(num_voting_inicial + 1 == num_voting_final and len(create_votings) == 2)   

    def voting_incorrect_copy_test(self):
        num_voting_inicial = len(Voting.objects.all())
        voting_id = 5
        c = Client()
        response = c.get(reverse('copy_voting', kwargs={'voting_id':voting_id}), {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        response.user = self.login()
        num_voting_final = len(Voting.objects.all())
        self.assertTrue(num_voting_inicial == num_voting_final)
        self.assertEqual(response.status_code, 404)     

#FIN TEST DAVID


##TEST MANU
    def create_voting_gobern_test(self):
        v = Voting(name="Votación Gobierno 2020", desc="Votación básica")
        v.save()

        self.assertEqual(v.pk != 0, True)

    def create_voting_gobern(self):
        v = Voting(name="Votación Gobierno 2020", desc="Votación básica")
        v.save()

        return v
    
    def create_voting_gobern_API_test(self):
        self.login()
        data = {'name': 'voting pass',
                'description': 'Votacion básica API'
                }
        response = self.client.post('/voting/edit/', data, format='json')

        self.assertEqual(response.status_code, 302)

    def create_voting_FULL_gobern_API_test(self):
        self.login()
        auths = Auth.objects.all()
        candidatures = CandidatesGroup.objects.all()
        data = {'name': 'voting pass',
                'description': 'Votacion básica API',
                'start_date_selected': '',
                'end_date_selected': '',
                'custom_url': '',
                'candidatures': candidatures,
                'auths': auths,
                }
        response = self.client.post('/voting/edit/', data, format='json')
        
        self.assertEqual(response.status_code, 302)

    def create_auths_API_test(self):
        self.login()
        data = {
            'auth_name': 'Auths prueba',
            'base_url': 'https://urlPrueba.co/token',
            'auth_me': True
        }
        response = self.client.post('/voting/create_auth/', data, format='json')
        
        self.assertEqual(response.status_code, 302)

    def create_auths_API_fail_test(self):
        self.login()
        data = {
            'auth_name': '',
            'base_url': '',
            'auth_me': ''
        }
        response = self.client.post('/voting/create_auth/', data, format='json')
        
        self.assertEqual(response.status_code, 302)

    def get_voting_json_API_test(self):
        v = self.create_voting_gobern()
        id_voting = v.pk

        response = self.client.get('/voting/view?id='+str(id_voting))
        self.assertEqual(response.status_code, 302)

###FIN TEST MANU


        #TEST ANTONI0
    def test_update_voting_start(self):        
        voting = self.create_voting() 

        #Votacion empezada correctamente
        data = {'action': 'start', 'voting_id': voting.pk}        
        response = self.client.post('/voting/votings/update/', data, format='json')   
        self.assertEqual(response.status_code, 302)


    def test_update_voting_stop(self):        
        voting = self.create_voting() 

        #Votacion parada correctamente
        data = {'action': 'start', 'voting_id': voting.pk}        
        response = self.client.post('/voting/votings/update/', data, format='json') 
        data = {'action': 'stop', 'voting_id': voting.pk}        
        response = self.client.post('/voting/votings/update/', data, format='json') 
        self.assertEqual(response.status_code, 302) 


    def test_update_voting_delete(self):        
        voting = self.create_voting()  

        #Votacion eliminada correctamente
        data = {'action': 'delete', 'voting_id': voting.pk}        
        response = self.client.post('/voting/votings/update/', data, format='json')
        self.assertEqual(response.status_code, 302)


    def test_update_multiple_voting_start(self):        
        voting = self.create_voting() 

        #Votacion empezada correctamente
        data = {'action_multiple': 'start', 'array_voting_id[]': voting.pk}        
        response = self.client.post('/voting/votings/update_selection/', data, format='json')   
        self.assertEqual(response.status_code, 302)


    def test_update_multiple_voting_stop(self):        
        voting = self.create_voting() 

        #Votacion parada correctamente
        data = {'action_multiple': 'start', 'array_voting_id[]': voting.pk}        
        response = self.client.post('/voting/votings/update_selection/', data, format='json') 
        data = {'action_multiple': 'stop', 'voting_id': voting.pk}        
        response = self.client.post('/voting/votings/update_selection/', data, format='json') 
        self.assertEqual(response.status_code, 302) 



    def test_update_multiple_voting_delete(self):        
        voting = self.create_voting()  

        #Votacion eliminada correctamente
        data = {'action': 'delete', 'array_voting_id[]': voting.pk}        
        response = self.client.post('/voting/votings/update_selection/', data, format='json')
        self.assertEqual(response.status_code, 302)

        ################################################

#TEST JUANMA
    def csv_validation_primaries_test(self):
        num_candidatos_inicial = len(Candidate.objects.all())

        path = str(os.getcwd()) + "/voting/files/candidatos-test-primarias.csv"
        with open(path, 'r') as archivo:
            csv = archivo.read() 
        c = Client()
        data = {'param': csv, 'candidature_name': "prueba"}
        request = c.post('/voting/validate/', data, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        http_content = str(request.content.decode('utf-8'))
        count_errors = http_content.count('El candidato Antonio no ha pasado el proceso de primarias')
        num_candidatos_final = len(Candidate.objects.all())
        self.assertTrue(count_errors == 1 and num_candidatos_inicial == num_candidatos_final)
    
    
    def csv_validation_provincias_test(self):
        num_candidatos_inicial = len(Candidate.objects.all())

        path = str(os.getcwd()) + "/voting/files/candidatos-test-provincias.csv"
        with open(path, 'r') as archivo:
            csv = archivo.read() 
        c = Client()
        data = {'param': csv, 'candidature_name': "prueba"}
        request = c.post('/voting/validate/', data, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        http_content = str(request.content.decode('utf-8'))
        count_errors = http_content.count('Tiene que haber al menos dos candidatos al congreso cuya provincia de nacimiento o de residencia tenga de código ML')

        num_candidatos_final = len(Candidate.objects.all())
        self.assertTrue(count_errors == 1 and num_candidatos_inicial == num_candidatos_final)

    def csv_validation_formato_test(self):
        num_candidatos_inicial = len(Candidate.objects.all())

        path = str(os.getcwd()) + "/voting/files/candidatos-test-formato.csv"
        with open(path, 'r') as archivo:
            csv = archivo.read() 
        c = Client()
        data = {'param': csv, 'candidature_name': "prueba"}
        request = c.post('/voting/validate/', data, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        http_content = str(request.content.decode('utf-8'))
        count_errors = http_content.count('Error en la línea 2: Hay errores de formato/validación')

        num_candidatos_final = len(Candidate.objects.all())
        self.assertTrue(count_errors == 1)


    def markdown_save_test(self):
        voting = Voting(name="Prueba123456789", desc="# Esto no se tiene que guardar como html y se traduce usando librerias")
        voting.save()
        voting_saved = Voting.objects.get(name="Prueba123456789")
        self.assertTrue(voting_saved.desc != markdown.markdown(voting_saved.desc))
#FIN TEST JUANMA

# class TestSignup(unittest.TestCase):

#     def setUp(self):
#         self.driver = webdriver.Firefox()
        
#     def test_custom_url(self):
#         self.driver.get("http://localhost:8000/admin/login/?next=/admin/")
#         self.driver.find_element_by_id('id_username').send_keys("practica")
#         self.driver.find_element_by_id('id_password').send_keys("practica")
        
#     #TEST JUANMA
#     def markdown_voting_form_test(self):
#         self.driver.get("http://localhost:8000/login/")
#         self.driver.find_element_by_name('username').send_keys("equipo")
#         self.driver.find_element_by_name('password').send_keys("decide1234")
#         self.driver.find_element_by_id("submit_login").click()

#         self.driver.get("http://localhost:8000/voting/edit/")
#         self.driver.find_element_by_id('markdownText').send_keys("# Prueba de HTML")
#         htmlRenderizado = self.driver.find_element_by_id('markdownRenderizado')
#         print(htmlRenderizado.get_attribute("innerHTML"))
#         self.assertTrue("<h1>Prueba de HTML</h1>" in htmlRenderizado.get_attribute("innerHTML"))

#     def markdown_voting_form_test(self):
#         self.driver.get("http://localhost:8000/login/")
#         self.driver.find_element_by_name('username').send_keys("equipo")
#         self.driver.find_element_by_name('password').send_keys("decide1234")
#         self.driver.find_element_by_id("submit_login").click()


#         self.driver.get("http://localhost:8000/voting/edit/")
#         self.driver.find_element_by_id('markdownText').send_keys("# Prueba de HTML")
#         self.driver.find_element_by_id("botonBorrar").click()
#         self.assertTrue(self.driver.find_element_by_id('markdownText').text == "")
# #FIN TEST JUANMA

#     def tearDown(self):
#         self.driver.quit

# if __name__ == '__main__':
#     unittest.main()
