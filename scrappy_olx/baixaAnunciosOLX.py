#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: jeovanio


Simples Web Crawling com Selenium para baixar anuncios selecionados do OLX


requeriments:
instalar geckodriver para o navegador que se quer usar, p.e.:
sudo apt install firefox-geckodriver

instalar o selenium:
pip install selenium

pip install psycopg2-binary
sudo apt install firefox-geckodriver

"""


from selenium import webdriver

import psycopg2

import logging
import time

import sys



##########################################################
# Le a pagina atual, carrega os elementos desejados, verifica se tem mais páginas e avança antes de retornar
# Se não tiver mais página, retorna 0, senao retorna numero proxima pagina

def LePagina(driver, url_pagina_inicial, page):

    lstRetorno = []

    
    driver.get(url_pagina_inicial+'&o='+str(page))


    lstCards = driver.find_elements("xpath","//section[@class='olx-adcard  olx-adcard__vertical undefined']")
 
    if len(lstCards)>0:
       bAchou = True
       print("Achei ",len(lstCards),"anúncios na página")
    else:
       print("Não Achei anuncios")
       bAchou = False

    for card in lstCards:
        
        #pega o preco do anuncio
        try:
            
            
            preco_div = card.find_element("xpath","./div/div[@class='olx-adcard__mediumbody']")
            #preco_elem = card.find_element("xpath","./div/div/h3[@class='typo-body-large olx-adcard__price font-semibold']")
            if preco_div:
                preco = preco_div.text
        except:        
            preco = "0"
            

        #Pega km e ano do anuncio
        try:
            km = ""
            ano = ""

            #testa primeiro se tem esses elementos
            det_elem = card.find_element("xpath","./div/div/div/div/div[@class='olx-adcard__detail']")         
            #se nao der erro, continua mas pega a lista com todos   
            if det_elem: 
                lstDetails = card.find_elements("xpath","./div/div/div/div/div[@class='olx-adcard__detail']")
                for d in lstDetails:
                    if "km" in d.text:
                        km = d.text
                    elif "Ano" in d.get_attribute("aria-label"):
                        ano = d.get_attribute("aria-label")
        except:
            km = ""
            ano = ""
            
                
        print(f"km={km} e ano={ano}")
            
        #pega o link do anuncio
        try:
            link_elem = card.find_element("xpath","./div/div/a[@class='olx-adcard__link']")         
            if link_elem: 
                href = link_elem.get_attribute("href")    
                cod_anuncio = href.split("-")[-1]
                titulo = link_elem.get_attribute("title")    
        except:
            cod_anuncio = "0"
            href = ""
            titulo = ""
            
        lstRetorno.append([cod_anuncio,titulo[0:70],ano,km,preco,href])
            
        print("anuncio:",titulo, ano, km, preco)

    #verifica se tem outra página
    try:
        paginacao = driver.find_element("id","listing-pagination")
    
        prox = paginacao.find_element("xpath","./div/a[text()='Próxima página']")
        
        #verifica se está habilitado
        class_name = prox.get_attribute("class")
        if "olx-core-button--disabled" not in class_name:
            temProxima = True
        else:
            temProxima = False
    except:
        temProxima = False
        
    if (temProxima):
        print("Tem mais página")        
        page += 1
        return page,lstRetorno
    else:
        return 0,lstRetorno
##############################################################################
def CarregaDadosOLX(logger, maxPages=1):
    

    
    logger.info("Abrindo sessao webdriver")
    driver = webdriver.Firefox()
    driver.implicitly_wait(30) # seconds
    logger.info("Abrindo pagina inicial")
    lstAnuncios = []
    
    try:
        
        page = 1
        pagina_inicial = "https://www.olx.com.br/autos-e-pecas/motos/estado-sc?ic=branding&local=banner-descubra&campaign=motoshmautos&message=home" 
        driver.get(pagina_inicial)
        
        print("\n verificar se já conseguiu abrir a página:")
        
        #x = input("Terminou de logar (S/N):")
    except:
        #print("*****  ERRO  execução captura web com RPA Selenium ****")
        logger.error("*****  ERRO  execução da primeira página com Selenium ****")
        x = input("Continuar e fechar a página após erro?")

        
    try:        
        
        div_total = driver.find_element("id","total-of-ads")
        
        cookie = driver.find_element("id","adopt-accept-all-button")
        
        if (cookie):
           
            cookie.click()    # aceita os cookies da página
        
        
        #Estabelecida a sessão corretamente
        
        #Lê cada pagina agora
        
        print ("inicio da execução")
        
        page,lstRetorno = LePagina(driver, pagina_inicial, 1)
        lstAnuncios.extend(lstRetorno)   
        
        while (page>0):
            
            #so para controle inicial
            if(page > maxPages): break
        
            print("Pagina:",page)    
        
        
            page,lstRetorno = LePagina(driver, pagina_inicial, page)
            lstAnuncios.extend(lstRetorno) 
            #print(lstRetorno)
            
            #repete o ciclo
            
        print("Fim da captura")
    except:
        #print("*****  ERRO  execução captura web com RPA Selenium ****")
        logger.error("*****  ERRO  execução captura web com RPA Selenium ****")
        x = input("Continuar e fechar a página após erro?")

    finally:
        driver.quit()



    return lstAnuncios





#####################################################################################
def ConectaBD_JeoLab():

    print('Conectando com BD do JeoLab para salvar no banco de dados do ADW...')

    ##### PostGres de LAB
    host='localhost'   #usa port-forward do kubectl para acessar ambiente azure
    port=5432          #usa port-forward do kubectl para acessar ambiente azure
    user = 'jeolab'
    dbname = 'jeolab'
    password='jeolab'
    
    
    conn_string = "host='"+host+"' dbname='"+dbname+"' user='"+user+"' password='"+password+"'"
    
    # print the connection string we will use to connect
    print ("Connecting to database <"+host+":"+str(port)+"> ...")
    
    #get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(dbname=dbname, host=host, user=user, password=password, port=port)
    
    print ("Connected!\n")
    
    return conn
#####################################################################################



#main

print("Baixando anuncios motos do OLX  - Santa Catarina")

logger = logging.getLogger('JeoLab_crawl_Sel')

lstAnuncios = []

lstAnuncios = CarregaDadosOLX(logger, 10)


if not lstAnuncios and len(lstAnuncios) > 0: 
    conn = ConectaBD_JeoLab()
    cursor = conn.cursor()

    print("BD conexão ok")

    #insere cada registro encontrado no anuncio no BD
    logger.info("Inserindo registros lidos no BD JeoLAB - tabela OLX_motos")

    logger.info("Ainda sem um mecanismo de update por diferença, deletando registros e reinserindo...")
    sql = 'DELETE FROM olx.OLX_motos where true'
    cursor.execute(sql)

    for a in lstAnuncios:
        sql = 'INSERT INTO olx.OLX_motos (cod_anuncio, titulo, modelo, km, tx_valor, img_url_src) VALUES ('
       
        for c in a[:-1]:
            sql += "'"+c+"',"
        sql += "'"+a[-1]+"');"    
        
        print(sql)
        # execute our Query
        cursor.execute(sql)
        
    conn.commit()
    conn.close()
    
 
   
