"""Reagrupaciones EXACTAS de la cubica de 35. Mismo polinomio, otra escritura."""
import sys
sys.path.insert(0,r'C:\Users\Usuario\eda\CapiMagics\designs\scripts')
from encoder_design import coeffs as C

NOM=['a','b','d','e']
def mono(ex,salta=()):
    return ''.join(NOM[i]+('' if ex[i]==1 else '^%d'%ex[i])
                   for i in range(4) if ex[i] and i not in salta)

def poly(pares,ancho=999):
    """pares = [(coef, texto_monomio)] -> cadena."""
    out=''
    for k,(v,t) in enumerate(pares):
        s=('%+.5f'%v) if not t else ('%+.5f%s'%(v,t))
        out+=(s if k==0 else ' '+s)
    return out

CO=list(zip(C.IEX_MIN,C.EXPONENTES))

print('#'*74)
print('## A) AGRUPADA: coeficientes que son polinomios en (Ll, L9)')
print('#'*74)
print()
print('  lg10 Iex(-) =')
grupos={}
for v,ex in CO:
    grupos.setdefault((ex[0],ex[1]),[]).append((v,ex))
orden=sorted(grupos,key=lambda k:(k[0]+k[1],k[0]))
for (i,j) in orden:
    ter=sorted(grupos[(i,j)],key=lambda x:-abs(x[0]))
    cab=mono((i,j,0,0)) if (i or j) else ''
    cuerpo=poly([(v,mono(ex,salta=(0,1))) for v,ex in ter])
    if cab: print('      + %-5s ( %s )'%(cab,cuerpo))
    else:   print('        %-5s   %s'%('',cuerpo))
print()
print('  10 lineas en vez de 7 apretadas, pero cada una dice algo: la primera es')
print('  la ley con Wd y Wl en su valor de referencia, y cada otra es COMO cambia')
print('  esa ley cuando los mueves.')
print()

print('#'*74)
print('## B) HORNER: anidada, la forma en que la evalua una maquina')
print('#'*74)
print()
def horner(ter,v):
    """ter = [(coef, ex)] con ex tupla de 4. Anida por la variable v hacia arriba."""
    if v==4:
        return '%+.5f'%(ter[0][0] if ter else 0.0)
    gmax=max((ex[v] for _,ex in ter),default=0)
    partes=[]
    for g in range(gmax,-1,-1):
        sub=[(c,ex) for c,ex in ter if ex[v]==g]
        partes.append(horner(sub,v+1) if sub else '0')
    s=partes[0]
    for g in range(1,len(partes)):
        s='(%s)*%s %s'%(s,NOM[v],partes[g]) if partes[g]!='0' else '(%s)*%s'%(s,NOM[v])
    return s
print('  lg10 Iex(-) =')
h=horner(CO,0)
ln='    '
for tok in h.split(' '):
    if len(ln)+len(tok)>72: print(ln); ln='    '
    ln+=tok+' '
print(ln)
print()
print('  Exacta y sin repetir una sola multiplicacion. Ilegible para un humano.')
print()

print('#'*74)
print('## C) UNA LINEA + TABLA (la forma canonica)')
print('#'*74)
print()
print('  lg10 Iex(-) = SUM  c[i,j,m,n] * a^i b^j d^m e^n     con i+j+m+n <= 3')
print()
print('  a=lg10(Wd)  b=lg10(Wl)  d=lg10(Ll)  e=lg10(L9)')
print()
print('  i j m n      c            i j m n      c            i j m n      c')
fil=[]
for v,ex in CO:
    fil.append('  %d %d %d %d %+11.5f'%(*ex,v))
for k in range(0,len(fil),3):
    print(''.join('%-38s'%x for x in fil[k:k+3]).rstrip())
import sys, itertools
import numpy as np
sys.path.insert(0,r'C:\Users\Usuario\eda\CapiMagics\designs\scripts')
from encoder_design import coeffs as C
NOMI=(0.725,0.947,0.394,1.811); X0=np.log10(np.array(NOMI))
EXP=[tuple(e) for e in C.EXPONENTES]
def base(Z): return np.column_stack([np.prod(Z**np.array(e),axis=1) for e in EXP])
rng=np.random.default_rng(0)
lo=np.log10([c[0] for c in C.CAJA]); hi=np.log10([c[1] for c in C.CAJA])
Z=rng.uniform(lo,hi,size=(6000,4))
VAR=['Wd','Wl','Ll','L9']
for nom,co,uni,esc in (('Iex(-)',C.IEX_MIN,'nA',1e9),('ganancia',C.GAIN,'',1.0),('V(a)',C.VA,'V',1.0)):
    y=base(Z)@np.array(co)
    c=np.linalg.lstsq(base(Z-X0),y,rcond=None)[0]
    k={e:v for v,e in zip(c,EXP)}
    c0=k[(0,0,0,0)]
    ex=[k[tuple(1 if i==j else 0 for i in range(4))] for j in range(4)]
    val=(10**c0*esc) if nom!='V(a)' else c0
    print('  %s en el nominal: %s'%(nom, ('%.1f %s'%(val,uni)) if nom!='V(a)' else '%.3f V'%val))
    print('     exponentes locales: '+'  '.join('%s %+0.3f'%(v,e) for v,e in zip(VAR,ex)))
    # error de esa forma de potencia en media caja
    m=np.array([1.0 if sum(e)<=1 else 0.0 for e in EXP])
    Z2=np.clip(rng.uniform(X0-(np.array(hi)-lo)/4,X0+(np.array(hi)-lo)/4,size=(4000,4)),lo,hi)
    y2=base(Z2)@np.array(co)
    r=base(Z2-X0)@(c*m)-y2
    er=(100*np.abs(10**r-1)).mean() if nom!='V(a)' else 1000*np.abs(r).mean()
    print('     esa potencia sola, en media caja: %.2f %s'%(er,'%' if nom!='V(a)' else 'mV'))
    print()
