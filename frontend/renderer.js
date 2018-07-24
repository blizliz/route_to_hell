const spawn = require("child_process").spawn;
const fs = require('fs');
const util = require('util');
const http = require('http');
const querystring = require('querystring');
const L = require('leaflet');

const writeFile = util.promisify(fs.writeFile);
const readFile = util.promisify(fs.readFile);

async function main() {
    try {
        const pid = await readFile('./daemon_pid', {encoding: 'utf8'});

        if (!isRunning(pid)) {
            await createDaemon();
        }
    } catch (e) {
        await createDaemon();
    }

    const form = document.getElementById("search_path");

    form.onsubmit = function (e) {
        e.preventDefault();
        const startLat = form.elements.start_lat.value;
        const startLon = form.elements.start_lon.value;
        const endLat = form.elements.end_lat.value;
        const endLon = form.elements.end_lon.value;

        const path =  querystring.stringify({
            startLat,
            startLon,
            endLat,
            endLon
        });

        http.get({
            port: 9123,
            path: `/?${path}`
        }, function (res) {
            let jsonStr = '';
            console.log(`STATUS: ${res.statusCode}`);
            console.log(`HEADERS: ${JSON.stringify(res.headers)}`);
            res.setEncoding('utf8');
            res.on('data', (chunk) => {
                jsonStr += chunk;
                console.log(`BODY: ${chunk}`);
            });
            res.on('end', () => {
                let resultObj = JSON.parse(jsonStr);
                console.log(resultObj);

                var mymap = L.map('mapid').setView([55.755814, 37.617635], 15);

                L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(mymap);

                var polyline = L.polyline(resultObj, {color: 'purple'}).addTo(mymap);

                mymap.fitBounds(polyline.getBounds());
            });
        }).on('error', (e) => {
            console.error(`problem with request: ${e.message}`);
        });
    }
}

function isRunning(pidStr) {
    const pid = parseInt(pidStr,10);

    if (isNaN(pid)) {
        return false;
    }

    try {
        return process.kill(pid, 0)
    }
    catch(e) {
        return e.code === 'EPERM'
    }
}

async function createDaemon() {
    const pyProcess = spawn(
        '../backend/venv/bin/python3.5',
        ["../backend/main.py"],
        {cwd: '../backend', detached: true, stdio: 'ignore'}
    );

    pyProcess.unref();

    await writeFile("./daemon_pid", pyProcess.pid);
}

main();