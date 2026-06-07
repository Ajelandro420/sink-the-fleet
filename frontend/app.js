const API_URL = "";
let jugador = "Anonimo";
let totalCasillas = 0;
let dificultad = 0;
let partidaActualId = null;

let bloc1, bloc2, bloc3, blocRanking, tableroDiv, mensajeVictoria, sonidos = {};

document.addEventListener('DOMContentLoaded', () => {
    bloc1 = document.getElementById('bloc1');
    bloc2 = document.getElementById('bloc2');
    bloc3 = document.getElementById('bloc3');
    blocRanking = document.getElementById('blocRanking');
    tableroDiv = document.getElementById('tablero');
    mensajeVictoria = document.getElementById('mensajeVictoria');

    sonidos = {
        tocado: document.getElementById('hit'),
        hundido: document.getElementById('sunken'),
        agua: document.getElementById('miss'),
        ganar: document.getElementById('win'),
        perder: document.getElementById('lose')
    };

    const btnInfoDificultad = document.getElementById('btnInfoDificultad');
    const modalInfo = document.getElementById('modalInfo');
    const btnCerrarModal = document.getElementById('btnCerrarModal');

    if (btnInfoDificultad && modalInfo && btnCerrarModal) {
        btnInfoDificultad.addEventListener('click', () => {
            modalInfo.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });

        function cerrarModal() {
            modalInfo.style.display = 'none';
            document.body.style.overflow = 'auto';
        }

        btnCerrarModal.addEventListener('click', cerrarModal);

        modalInfo.addEventListener('click', (e) => {
            if (e.target === modalInfo) {
                cerrarModal();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modalInfo.style.display === 'flex') {
                cerrarModal();
            }
        });
    }

    console.log('DOMContentLoaded ==> Elementos inicializados');
});

function reproducirSonido(tipo) {
    if (sonidos[tipo]) {
        sonidos[tipo].currentTime = 0;
        sonidos[tipo].play().catch(e => console.log('Error reproduciendo sonido:', e))
        console.log(`reproducirSonido() ==> Sonido reproducido: ${tipo}`);
    }
}

function registrarMovimiento(texto) {
    const lista = document.getElementById("listaMovimientos");
    const li = document.createElement("li");
    li.textContent = texto;
    lista.prepend(li);
    console.log(`registrarMovimiento() ==> Movimiento registrado: ${texto}`);
}

async function cargarRanking() {
    try {
        const res = await fetch(`${API_URL}/ranking`);
        const data = await res.json();

        const rankingList = document.getElementById("ranking");
        rankingList.innerHTML = "";

        if (data.length === 0) {
            rankingList.innerHTML = "<li>No hay partidas aún</li>";
            return;
        }

        data.slice(0, 10).forEach((item, i) => {
            const li = document.createElement("li");
            li.textContent = `${i + 1}. ${item.jugador} — ${item.puntuacion} pts`;
            rankingList.appendChild(li);
            console.log(`cargarRanking() ==> Ranking cargado: ${li.textContent}`);
        });

        console.log("cargarRanking() ==> Ranking completo cargado");
    } catch (e) {
        console.error("cargarRanking() ==> Error cargando ranking:", e);
        document.getElementById("ranking").innerHTML = "<li>Error al cargar ranking</li>";
    }
}

document.getElementById('btnComencar').addEventListener('click', async () => {
    const filas = parseInt(document.getElementById('files').value);
    const columnas = parseInt(document.getElementById('columnes').value);
    totalCasillas = filas * columnas;
    dificultad = document.querySelector('input[name="dificultat"]:checked').value;

    jugador = document.getElementById('jugador').value || "Anònim";

    try {
        const response = await fetch(`${API_URL}/crearPartida`, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({filas,columnas,jugador})
        });
        const data = await response.json();
        partidaActualId = data.id_partida;

        mostrarBlocs(filas,columnas);
        cargarRanking();
        console.log(`dom.btnComenzar(click) ==> Iniciada nueva partida con ID: ${partidaActualId}`);
    } catch(e){console.error(e);}
});

document.getElementById('btnAbandonar').addEventListener('click', reiniciarJuego);

function reiniciarJuego() {
    partidaActualId = null;

    bloc2.style.display = "none";
    bloc3.style.display = "none";
    blocRanking.style.display = "none";
    bloc1.style.display = "flex";

    tableroDiv.innerHTML = "";

    document.getElementById('dispars').textContent = "0";
    document.getElementById('encerts').textContent = "0";
    document.getElementById('enfonsats').textContent = "0";
    document.getElementById('puntuacio').textContent = "0";

    mensajeVictoria.style.display = "none";

    try {
        fetch(`${API_URL}/abandonar`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({partida_id: partidaActualId})
        });
    } catch (e) {console.error(e);}
    console.log("reiniciarJuego() ==> Juego reiniciado");
}

function mostrarBlocs(filas,columnas){
    bloc1.style.display="none";
    bloc2.style.display="flex";
    bloc3.style.display="flex";
    blocRanking.style.display="flex";
    generarTablero(filas,columnas);
    console.log('mostrarBlocs() ==> Bloques mostrados');
}

function generarTablero(filas,columnas){
    tableroDiv.style.gridTemplateColumns = `repeat(${columnas},1fr)`;
    tableroDiv.style.gridTemplateRows = `repeat(${filas},1fr)`;
    tableroDiv.innerHTML = '';
    for(let i=0;i<filas;i++){
        for(let j=0;j<columnas;j++){
            const c=document.createElement('div');
            c.className='casilla';
            c.dataset.fila=i;
            c.dataset.columna=j;

            c.setAttribute('role', 'button');  
            c.setAttribute('aria-label', `Casilla fila ${i+1}, columna ${j+1}`);  
            c.setAttribute('tabindex', '0');  
            
            c.addEventListener('click',()=>dispararCasilla(i,j,c));
            
            c.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    dispararCasilla(i, j, c);
                }
            });

            console.log(`generarTablero() ==> Casilla creada en fila ${i}, columna ${j}`);
            tableroDiv.appendChild(c);
        }
        console.log(`generarTablero() ==> Fila ${i} creada`);
    }
    console.log('generarTablero() ==> Tablero generado');
}

function perder() {
    reproducirSonido('perder');
    mensajeVictoria.textContent=`¡Lo siento, ${jugador}! Has alcanzado el límite de disparos.`;
    mensajeVictoria.style.display='block';
    setTimeout(()=>mensajeVictoria.style.display='none',3000);
    document.querySelectorAll('.casilla').forEach(c=>c.classList.add('disparada'));
    console.log('perder() ==> Has perdido la partida');
    cargarRanking();
}

function ganar() {
    reproducirSonido('ganar');
    mensajeVictoria.textContent=`¡Felicidades, ${jugador}! Has hundido todos los barcos.`;
    mensajeVictoria.style.display='block';
    setTimeout(()=>mensajeVictoria.style.display='none',3000);
    document.querySelectorAll('.casilla').forEach(c=>c.classList.add('disparada'));
    console.log('ganar() ==> ¡Has ganado la partida!');
    cargarRanking();
}

async function dispararCasilla(fila,columna,casilla){
    if(casilla.classList.contains('disparada') || casilla.classList.contains('hundido')) return;

    //Validamos
    if (!partidaActualId) {
        alert('Error: No hay partida activa');
        console.log('dispararCasilla() ==> Error: No hay partida activa');
        return;
    }

    try{
        const r=await fetch(`${API_URL}/disparar?fila=${fila}&columna=${columna}&partida_id=${partidaActualId}`,{method:'POST'});
        const data=await r.json();

        casilla.classList.add('disparada');
        casilla.style.cursor='not-allowed';

        if(data.resultado==='repetido'){
            alert('¡Ya has disparado a esta casilla! Elige otra.');
            console.log(`dispararCasilla() ==> Disparo repetido en fila ${fila}, columna ${columna}`);
            return;
        }
        else if(data.resultado==='tocado') {
            casilla.classList.add('tocado');
            casilla.textContent='💥';

            casilla.setAttribute('aria-label', `Tocado en fila ${fila+1}, columna ${columna+1}`);  

            reproducirSonido('tocado');
            registrarMovimiento(`💥 Tocado en (${fila+1}, ${columna+1})`);
            console.log(`dispararCasilla() ==> Tocado en fila ${fila}, columna ${columna}`);

        }
        else if(data.resultado==='hundido') {
            casilla.classList.add('hundido');
            casilla.textContent='☠️';

            casilla.setAttribute('aria-label', `Hundido en fila ${fila+1}, columna ${columna+1}`);  

            reproducirSonido('hundido');
            registrarMovimiento(`☠️ Hundido en (${fila+1}, ${columna+1})`);
            console.log(`dispararCasilla() ==> Hundido en fila ${fila}, columna ${columna}`);
        }
        else {
            casilla.classList.add('agua');
            casilla.textContent='💧';

            casilla.setAttribute('aria-label', `Agua en fila ${fila+1}, columna ${columna+1}`);  

            reproducirSonido('agua');
            registrarMovimiento(`💧 Agua en (${fila+1}, ${columna+1})`);
            console.log(`dispararCasilla() ==> Agua en fila ${fila}, columna ${columna}`);
        }

        document.getElementById('dispars').textContent=data.dispars;
        document.getElementById('encerts').textContent=data.encerts;
        document.getElementById('enfonsats').textContent=data.vaixells_hundidos;
        document.getElementById('puntuacio').textContent=data.puntuacio;

        if(data.victoria){
            ganar();
            return;
        }

        switch (dificultad) {
            case '1':
                if (Number(data.dispars)>= totalCasillas*0.80){
                    perder();
                }
                break;

            case '2':
                if (Number(data.dispars)>= totalCasillas*0.65){
                    perder();
                }
                break;

            case '3':
                if (Number(data.dispars)>= totalCasillas*0.50){
                    perder();
                }
                break;
        }
    } catch(e){console.error(e);}
}