# -*- coding: utf-8 -*-
### required - do no delete
def user(): return dict(form=auth())
#def download(): return response.download(request,db)
#def call(): return service()
### end requires
#def index():
 #   return dict()

#def error():
 #   return dict()
from gluon.tools import fetch  
from time import sleep
from random import randrange
import re
listf=[]
count=0
bigans=[]# store the final ouput to be passed into the view
@auth.requires_login()    #login reqired to access index page
def index():
    form=SQLFORM(db.input) #displays the form to user for taking the input from the user
    if form.process().accepted:
        response.flash = 'Login successful'
        redirect(URL('final_ans'))
    return dict(form=form)
def extract1(url,l1): #extracts the top_result urls from the first page
    ret=[]
    html=fetch(url) #fetches the html page of the given url ans stores it in a string html
    html_splitted=html.split("<A HREF=\"citation.cfm") #splitting the fetched string
    ht=html_splitted[0]
    del html_splitted[0]
    k=html_splitted[0].split('>')
    if k[1][:-3]==l1[0]:#if the user inputs title of a paper
        k=html_splitted[0].find('\"')
        s="http://dl.acm.org/citation.cfm"+html_splitted[0][:k]
        ret.append(s.split('&preflayout')[0]+'&preflayout=flat')
    else: #if user inputs some keywords
        for i in range(0,l1[2]):
            k=html_splitted[i].find('\"')
            s="http://dl.acm.org/citation.cfm"+html_splitted[i][:k]
            ret.append(s.split('&preflayout')[0]+'&preflayout=flat')
    return ret
def sorting():
    bigans=[]   #stores final output in a list
    l1=u_filter() #stores the user input in list l1
    url="http://dl.acm.org/results.cfm?h=1&query="+'+'.join(l1[0].split()) #construct corresponding url
    fst_l=[]
    ret1=[]
    fst_l=extract1(url,l1) #extracts the urls of query results and stores it in a list fst_l
    rec(fst_l,l1,bigans)  #this function recursively fetches the required information and stores every result in list bigans.
    if request.args(0)=='0':  #if the list needs to be sorted by relevence,the bigans doesnt change.
        pass
    else:
        bigans=sorted(bigans,key=lambda x:(x[4][6:]*360+x[4][:2]*30+x[4][3:5]),reverse=True)    #if the list needs to be sorted according to release date,it is sorted by sorted() python inbuilt function.
    au=db(auth.user.username==db.auth_user.username).select().first()   
    email=au.email        #email of user who is logged in is extracted.
    return dict(bigans=bigans,level=l1[1],top=l1[2],ret1=ret1,email=email)   
def final_ans():
    bigans=[] #stores the final output in a list
    l1=u_filter() #extracting the user input in a list
    url="http://dl.acm.org/results.cfm?h=1&query="+'+'.join(l1[0].split()) #forming the url
    fst_l=[]
    ret1=[]
    fst_l=extract1(url,l1)     #extracts the urls of query results and stores it in a list fst_l
    rec(fst_l,l1,bigans)  #this function recursively fetches the required information and stores every result in list bigans.
    au=db(auth.user.username==db.auth_user.username).select().first()
    email=au.email       #email of user who is logged in is extracted.
    return dict(bigans=bigans,level=l1[1],top=l1[2],ret1=ret1,email=email)
def rec(list1,l1,bigans):     #recursion that results the tree of citations.
    global count #variable for level of recursion.
    count=count+1
    global listf
    listf.append([])
    for x in list1:
        if x!='':
            sleep(randrange(1,5))      #this is to avoid flooding the target url by multiple requests with less time gap.
            z=cite(x)               #parsing the url x and storing it in a list z
            bigans.append(z)        #stores that information in bigans
            if count < l1[1]:            #if level of recursion is less than user input only then continue recursion else return
                rec(z[7],l1,bigans[-1])     #recursive calls
    count=count-1
    return
def cite(url):
    if url=='':
        return []
    l1=u_filter()
    html=fetch(url)
    temp=[]
    d=re.search('<meta name="citation_title"[\w\W]*?>',html).group()
    d=bold(d)
    temp.append(d.split('=')[2][1:-2])
    temp.append(url)
    f=re.search('\"ft_gateway.cfm[\w\W]*?\"',html)
    if f!=None:
        f=f.group()
        f=bold(f)
        temp.append('http://dl.acm.org/'+f[1:-1])
    else:
        temp.append(url)
    c=re.search('<meta name="citation_authors"[\w\W]*?>',html).group()
    c=bold(c)
    if l1[3]==1:
        temp.append(c.split('=')[2][1:-2])
    else:
        temp.append(-1)
    b=re.search('<meta name="citation_date"[\w\W]*?>',html).group()
    b=bold(b)
    if l1[5]==1:
        temp.append(b.split('=')[2][1:-2])
    else:
        temp.append(-1)
    h=re.search('<A NAME="abstract" class="small-text">ABSTRACT[\w\W]*?</div>',html)
    if h!=None:
        h=h.group()
        h=bold(h)
        if 'An abstract is not available.' in h:
            h1="An abstract is not available."
        elif '<div style=\"display:inline\">' in h:

            h1=h.split('<div style=\"display:inline\">')[1]
            h1=remove(h1)
        else:
            h=h.replace('</A></h1>','')
            h=remove(h)
            h1=h.split('>')[1]
    else:
        h1=-1
    temp.append(h1)
    s=re.search('CITED BY[\w\W]*?INDEX TERMS',html).group()
    if 'Citings are not available' not in s:
        e=re.search('\d* Citations',s)
        if l1[4]!=1:
            temp.append(-1)
        elif e!=None:
            temp.append(e.group().split()[0])
        else:                                                                            
            temp.append(1)
        i=0
        cit=[]
        while i < l1[2]:
            i+=1
            s1=re.search('<a href[\w\W]*?</a>',s)
            if s1==None:
                cit.append('')
            elif s1!=None:
                k=s.find(s1.group())
                cit.append(("http://dl.acm.org/"+s1.group().split('\"')[1]).split('&preflayout')[0]+'&preflayout=flat')
                s=s[k+2:]
           
        temp.append(cit)
    else:
        if l1[4]==1:
            temp.append(0)
        else:
            temp.append(-1)
        temp.append([])
    return temp
def u_filter():
    inpu=db().select(db.input.ALL)  #selects the last entry in the database table
    for inp in inpu:
        key=inp.keywords                    #stores each entry of database into a variable
        level=inp.Recursion_levels
        top=inp.Top_results
        auth=inp.Show_author
        cited_by=inp.Show_no_of_citations
        year=inp.Show_release_date
    return [key,level,top,auth,cited_by,year]      #returns a list
def bold(d):              #this function removes the unwanted bold tags from the html page extracted
    pre=""
    while pre!=d:
        pre=d
        d=d.replace("<b>","")
        d=d.replace("</b>","")
    return d
def remove(d):          #this function removes unwanted html tags from text.
    pre=""
    while pre!=d:                     #removes paragraph tags
        pre=d
        d=d.replace("<p>","")
        d=d.replace("</p>","")
    pre=""
    while pre!=d:                     #removes div tags
        pre=d
        d=d.replace("<div style=\"display:inline\">","") 
        d=d.replace("</div>","")
    pre=""
    while pre!=d:                     #removes br tags
        pre=d
        d=d.replace("<br>","")
    pre=""
    while pre!=d:                     #removes par tags
        pre=d
        d=d.replace("<par>","")
        d=d.replace("</par>","")
    return d            #returns the filtered text
def abstract1():
    abss=request.args[0]
    pre=""
    while pre!=abss:
        pre=abss
        abss=abss.replace("_"," ")
    abss1=abss.split(".")       
    return dict(abss1=abss1)
