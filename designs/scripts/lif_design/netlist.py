"""El esquematico de referencia, emitido desde el mismo diseño que el layout.

En un flujo a mano el LVS es un DESCUBRIMIENTO: se dibuja el esquematico por
un lado, el layout por otro, y la comparacion revela si divergieron. Aqui es
una COMPROBACION: las dos salidas vienen de la misma NeuronDesign, asi que un
fallo solo puede significar un bug del generador. La clase de fallo "alguien
tecleo distinto en dos sitios" no existe.

La topologia es fija -- tres inversores, el interruptor M5 y el banco de MIM --
y lo unico que el solver decide son cuatro dimensiones y cuantos condensadores.

Los nombres de nodo son los que `_pin_labels` marca en el GDS: sin esa
correspondencia el extractor nombra las redes por su cuenta y el LVS compara
etiquetas que no existen.
"""
from __future__ import annotations

from . import mim as mim_pdk

# Nodos internos. `integration` es la membrana y va al pin Iin -- la fuente de
# corriente entra ahi, asi que el nodo del integrador ES el puerto de entrada.
_RESET = "spike/reset"


def de_diseño(design, handles, name: str = "lif") -> str:
    """Netlist SPICE del diseño, para comparar contra el GDS.

    Todas las cifras salen de `handles`, no de `design`: son las del generador,
    ya subidas a la rejilla del GDS, y el modelo del MIM depende de donde el
    PDK ponga capmet. `design` se mantiene en la firma porque es lo que
    identifica de que diseño es este netlist.
    """
    del design  # la topologia es fija; las dimensiones vienen de handles
    # Lo DIBUJADO, no lo pedido: from_design sube cada dimension a la rejilla
    # del GDS, y el comparador ve el ancho que hay en el layout.
    d = handles["dims"]
    w_inv, l_inv = d["W_inv"], d["L_inv"]   # los inversores van al minimo
    n_caps = len(handles["caps"])
    lado = float(handles["cap_lado"])

    def fet(nombre, d, g, s, b, tipo, w, l):
        return ("M%s %s %s %s %s %s L=%gu W=%gu nf=1 m=1"
                % (nombre, d, g, s, b, tipo, l, w))

    lineas = [
        ".subckt %s Vdd Vss Iin spike spike_neg" % name,
        "*.PININFO Vdd:B Vss:B Iin:I spike:O spike_neg:O",
        # inversor 0: la membrana lo excita, su salida es spike_neg
        fet("1", "spike_neg", "Iin", "Vdd", "Vdd", "pfet_03v3", w_inv, l_inv),
        fet("2", "spike_neg", "Iin", "Vss", "Vss", "nfet_03v3", w_inv, l_inv),
        # inversor 1: cierra el lazo de reset sobre la puerta de M5
        fet("3", _RESET, "spike_neg", "Vdd", "Vdd", "pfet_03v3", w_inv, l_inv),
        fet("4", _RESET, "spike_neg", "Vss", "Vss", "nfet_03v3", w_inv, l_inv),
        # inversor 2: el bufer de salida, el unico que el solver dimensiona
        fet("7", "spike", "spike_neg", "Vdd", "Vdd", "pfet_03v3",
            d["W_buf"], l_inv),
        fet("8", "spike", "spike_neg", "Vss", "Vss", "nfet_03v3",
            d["W_buf"], l_inv),
        # M5, el interruptor que descarga la membrana
        fet("5", "Iin", _RESET, "Vss", "Vss", "nfet_03v3",
            d["W_reset"], d["L_reset"]),
        # el banco. m=n en vez de n instancias: el comparador combina
        # dispositivos en paralelo, asi que las dos formas casan con la
        # extraccion, y una sola linea dice lo que hay.
        #
        # W/L/M, no c_width/c_length: el lector del deck de gf180
        # (custom_classes.lvs) traduce W*L*M -> area y (W+L)*M*2 -> perimetro,
        # que es con lo que compara. Cualquier otro nombre lo ignora en
        # silencio y el condensador entra con area cero.
        "XC1 Iin Vss %s W=%gu L=%gu M=%d"
        % (mim_pdk.modelo_lvs(), lado, lado, n_caps),
        ".ends",
    ]
    return "\n".join(lineas) + "\n"
