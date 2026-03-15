const SUPABASE_URL = 'https://bqergkmgcauypelsvohc.supabase.co';
const SUPABASE_KEY = 'sb_publishable_v2LGPra6wnORPbPKDF1RBw_WxYdltEf';
mapboxgl.accessToken = 'pk.eyJ1IjoiZGF2aWRjMTkwNyIsImEiOiJjbW1xZnE4c24wd2M2MnBzZHAxZTJ3OGdkIn0.DuQ9I53OqjAt4m2k4JzYqg';

const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/davidc1907/cmmqg2h8e000k01qq6s9p11gl',
    center: [10, 51],
    zoom: 4.5
});

let activePlanes = {
    "type": "FeatureCollection",
    "features": []
};

function processSighting(newSighting) {
    if (newSighting.lat && newSighting.lon) {
        const index = activePlanes.features.findIndex(f => f.properties.hex === newSighting.hex_code);

        if (index > -1) {
            const planeFeature = activePlanes.features[index];

            if (!planeFeature.properties.pathHistory) {
                planeFeature.properties.pathHistory = [planeFeature.properties.targetCoords];
            }

            planeFeature.properties.pathHistory.push([newSighting.lon, newSighting.lat]);

            planeFeature.properties.targetCoords = [newSighting.lon, newSighting.lat];
            planeFeature.properties.hdg = newSighting.hdg;
            planeFeature.properties.lastSeen = Date.now();
            planeFeature.properties.callsign = newSighting.callsign;

            updatePathsSource();

        } else {
            const feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [newSighting.lon, newSighting.lat]
                },
                "properties": {
                    "callsign": newSighting.callsign,
                    "hex": newSighting.hex_code,
                    "hdg": newSighting.hdg,
                    "lastSeen": Date.now(),
                    "currentCoords": [newSighting.lon, newSighting.lat],
                    "targetCoords": [newSighting.lon, newSighting.lat],
                    "pathHistory": [[newSighting.lon, newSighting.lat]]
                }
            };
            activePlanes.features.push(feature);
        }
    }
}

function updatePathsSource() {
    if (!map.getSource('paths-source')) return;

    const pathsData = {
        "type": "FeatureCollection",
        "features": activePlanes.features
            .filter(f => f.properties.pathHistory && f.properties.pathHistory.length > 1)
            .map(f => ({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": f.properties.pathHistory
                },
                "properties": {
                    "hex": f.properties.hex
                }
            }))
    };
    map.getSource('paths-source').setData(pathsData);
}

function animatePlanes() {
    let needsUpdate = false;

    activePlanes.features.forEach(f => {
        const current = f.properties.currentCoords;
        const target = f.properties.targetCoords;

        if (current && target) {
            const dx = target[0] - current[0];
            const dy = target[1] - current[1];

            if (Math.abs(dx) > 0.00001 || Math.abs(dy) > 0.00001) {
                current[0] += dx * 0.05;
                current[1] += dy * 0.05;

                f.geometry.coordinates = [current[0], current[1]];
                needsUpdate = true;
            }
        }
    });

    if (needsUpdate) {
        map.getSource('planes-source').setData(activePlanes);
    }

    requestAnimationFrame(animatePlanes);
}

map.on('load', async () => {
    await new Promise((resolve, reject) => {
        map.loadImage('plane.png', (error, image) => {
            if (error) {
                console.error("Error with loading the img:", error);
                reject(error);
                return;
            }
            map.addImage('plane-icon', image);
            resolve();
        });
    });

    map.addSource('planes-source', {
        type: 'geojson',
        data: activePlanes
    });

    map.addSource('paths-source', {
        type: 'geojson',
        data: {
            "type": "FeatureCollection",
            "features": []
        }
    });

    map.addLayer({
        id: 'paths-layer',
        type: 'line',
        source: 'paths-source',
        layout: {
            'line-join': 'round',
            'line-cap': 'round'
        },
        paint: {
            'line-color': '#ffffff',
            'line-width': 2,
            'line-opacity': 0.6
        },
        filter: ['==', 'hex', '']
    });

    map.addLayer({
        id: 'planes-layer',
        type: 'symbol',
        source: 'planes-source',
        layout: {
            'icon-image': 'plane-icon',
            'icon-size': 0.8,
            'icon-allow-overlap': true,
            'icon-rotate': ['get', 'hdg']
        }
    });

    map.on('click', 'planes-layer', (e) => {
        const coordinates = e.features[0].geometry.coordinates.slice();
        const callsign = e.features[0].properties.callsign;
        const hex = e.features[0].properties.hex;

        map.setFilter('paths-layer', ['==', 'hex', hex]);

        new mapboxgl.Popup()
            .setLngLat(coordinates)
            .setHTML(`
                <div style="color: #000; font-family: 'Inter', sans-serif;">
                    <strong style="font-size: 1.1em;">${callsign}</strong><br>
                    <span style="color: #666; font-size: 0.9em;">HEX: ${hex}</span>
                </div>
            `)
            .addTo(map);
    });

    map.on('click', (e) => {
        const features = map.queryRenderedFeatures(e.point, { layers: ['planes-layer'] });

        if (!features.length) {
            map.setFilter('paths-layer', ['==', 'hex', '']);
        }
    });

    map.on('mouseenter', 'planes-layer', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'planes-layer', () => {
        map.getCanvas().style.cursor = '';
    });

    const { data } = await supabaseClient
        .from('sightings')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(100);

    if (data) {
        data.reverse().forEach(sighting => {
            processSighting(sighting);
        });

    }

    supabaseClient
        .channel('public:sightings')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'sightings' }, payload => {
            processSighting(payload.new);
        })
        .subscribe();

    animatePlanes();

    setInterval(() => {
        const now = Date.now();
        const timeout = 2 * 60 * 60 * 1000;

        const oldLength = activePlanes.features.length;

        activePlanes.features = activePlanes.features.filter(f => (now - f.properties.lastSeen) < timeout);

        if (activePlanes.features.length < oldLength) {
            map.getSource('planes-source').setData(activePlanes);
        }
    }, 60000);
});