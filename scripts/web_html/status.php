<?php
// ============================================================
// Biomedical Hub — Service Status Dashboard
// Auto-detects host OS · Shows hosting location per service
// ============================================================

// ── Detect Host OS from mounted /etc/os-release ─────────────
function detectHostOS(): array {
    $info = ['name' => 'Unknown', 'id' => 'unknown', 'pretty' => 'Unknown OS', 'version' => ''];

    // Read kernel version from /proc/version
    $procFile = '/host-proc-version';
    $kernel = '';
    if (file_exists($procFile)) {
        $kernel = trim(file_get_contents($procFile));
        $info['kernel'] = $kernel;
    }

    // Read host's os-release (mounted from VM host)
    $osFile = '/host-os-release';
    if (file_exists($osFile)) {
        $lines = file($osFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        $kv = [];
        foreach ($lines as $line) {
            if (strpos($line, '=') !== false) {
                [$k, $v] = explode('=', $line, 2);
                $kv[trim($k)] = trim($v, '"\'');
            }
        }
        $info['pretty']  = $kv['PRETTY_NAME'] ?? $kv['NAME'] ?? 'Unknown';
        $info['name']    = $kv['NAME']        ?? 'Unknown';
        $info['id']      = strtolower($kv['ID'] ?? 'unknown');
        $info['version'] = $kv['VERSION_ID']  ?? '';
    }

    // Check if we are running in Docker Desktop on a Windows host
    if (
        strpos(strtolower($kernel), 'microsoft') !== false ||
        strpos(strtolower($kernel), 'wsl') !== false ||
        (isset($info['pretty']) && $info['pretty'] === 'Docker Desktop')
    ) {
        $info['name']   = 'Windows';
        $info['id']     = 'windows';
        $info['pretty'] = 'Windows Host (WSL2)';
    }

    return $info;
}

// ── Detect Docker Compose project name ──────────────────────
function detectDockerContext(): string {
    // The compose project name is typically the directory name
    // We can read it from /.dockerenv or environment
    $composeProject = getenv('COMPOSE_PROJECT') ?: '';
    if (!$composeProject) {
        // Try to infer from hostname
        $hostname = gethostname();
        return $hostname ?: 'docker';
    }
    return $composeProject;
}

// ── OS Icon ─────────────────────────────────────────────────
function osIcon(string $id): string {
    return match(true) {
        str_contains($id, 'arch')    => '🐧',
        str_contains($id, 'fedora')  => '🎩',
        str_contains($id, 'ubuntu')  => '🟠',
        str_contains($id, 'debian')  => '🌀',
        str_contains($id, 'windows') => '🪟',
        default                      => '🐧',
    };
}

$hostOS = detectHostOS();
$osIcon = osIcon($hostOS['id']);

// ── Hosting badges ───────────────────────────────────────────
$DOCKER_BADGE   = "Docker · {$osIcon} {$hostOS['name']}";
$WINDOWS_BADGE  = "🪟 Windows Host";

// ── Service definitions ──────────────────────────────────────
$GATEWAY = '172.17.0.1';

$services = [
    [
        'group' => 'Desarrollo y Simulación Biomédica',
        'icon'  => '🩺',
        'items' => [
            [
                'name'       => 'BiosenseLink (PoC)',
                'host'       => 'host-only',
                'port'       => 8081,
                'url'        => 'http://localhost:8081',
                'tag'        => 'FastAPI',
                'container'  => 'python server.py',
                'hosted_on'  => $WINDOWS_BADGE,
            ],
            [
                'name'       => 'HAPI FHIR Server',
                'host'       => 'hapi-fhir-server',
                'port'       => 8080,
                'url'        => 'http://localhost:8080',
                'tag'        => 'FHIR R4',
                'container'  => 'hapi-fhir-server',
                'hosted_on'  => $DOCKER_BADGE,
            ],
            [
                'name'       => 'Sensing Server UI',
                'host'       => 'sensing-server-1',
                'port'       => 3000,
                'url'        => 'http://localhost:3030/ui/index.html',
                'tag'        => 'IoMT',
                'container'  => 'sensing-server-1',
                'hosted_on'  => $DOCKER_BADGE,
            ],
        ]
    ],
    [
        'group' => 'Inteligencia Artificial',
        'icon'  => '🤖',
        'items' => [
            [
                'name'       => 'Ollama (LLMs)',
                'host'       => $GATEWAY,
                'port'       => 11434,
                'url'        => 'http://localhost:11434',
                'tag'        => 'IA Local',
                'container'  => 'nativo',
                'hosted_on'  => "{$osIcon} {$hostOS['name']} (nativo)",
            ],
            [
                'name'       => 'n8n Automation',
                'host'       => 'n8n_automation',
                'port'       => 5678,
                'url'        => 'http://localhost:5678',
                'tag'        => 'Flujos',
                'container'  => 'n8n_automation',
                'hosted_on'  => $DOCKER_BADGE,
            ],
        ]
    ],
    [
        'group' => 'Bases de Datos',
        'icon'  => '🗄️',
        'items' => [
            [
                'name'       => 'PostgreSQL',
                'host'       => 'clinical-postgres-db',
                'port'       => 5432,
                'url'        => 'http://localhost:5050',
                'tag'        => 'TCP :5432',
                'container'  => 'clinical-postgres-db',
                'hosted_on'  => $DOCKER_BADGE,
            ],
            [
                'name'       => 'pgAdmin 4',
                'host'       => 'clinical-pgadmin-web',
                'port'       => 80,
                'url'        => 'http://localhost:5050',
                'tag'        => 'Web UI',
                'container'  => 'clinical-pgadmin-web',
                'hosted_on'  => $DOCKER_BADGE,
            ],
            [
                'name'       => 'MySQL',
                'host'       => 'mysql_db',
                'port'       => 3306,
                'url'        => 'http://localhost:8082',
                'tag'        => 'TCP :3306',
                'container'  => 'mysql_db',
                'hosted_on'  => $DOCKER_BADGE,
            ],
            [
                'name'       => 'phpMyAdmin',
                'host'       => 'phpmyadmin_client',
                'port'       => 80,
                'url'        => 'http://localhost:8082',
                'tag'        => 'Web UI',
                'container'  => 'phpmyadmin_client',
                'hosted_on'  => $DOCKER_BADGE,
            ],
        ]
    ],
    [
        'group' => 'Gestión Documental',
        'icon'  => '📄',
        'items' => [
            [
                'name'       => 'Paperless-ngx',
                'host'       => 'paperless_webserver',
                'port'       => 8000,
                'url'        => 'http://localhost:8010',
                'tag'        => 'OCR',
                'container'  => 'paperless_webserver',
                'hosted_on'  => $DOCKER_BADGE,
            ],
            [
                'name'       => 'Gotenberg (PDF)',
                'host'       => 'gotenberg',
                'port'       => 3000,
                'url'        => 'http://localhost:3000',
                'tag'        => 'PDF',
                'container'  => 'gotenberg',
                'hosted_on'  => $DOCKER_BADGE,
            ],
        ]
    ],
    [
        'group' => 'Infraestructura',
        'icon'  => '⚙️',
        'items' => [
            [
                'name'       => 'Homer Dashboard',
                'host'       => 'homer',
                'port'       => 8080,
                'url'        => 'http://localhost:8085',
                'tag'        => 'Hub',
                'container'  => 'homer',
                'hosted_on'  => $DOCKER_BADGE,
            ],
            [
                'name'       => 'Portainer CE',
                'host'       => 'portainer',
                'port'       => 9000,
                'url'        => 'http://localhost:9000',
                'tag'        => 'Docker UI',
                'container'  => 'portainer',
                'hosted_on'  => $DOCKER_BADGE,
            ],
            [
                'name'       => 'Apache Web Server',
                'host'       => '127.0.0.1',
                'port'       => 80,
                'url'        => 'http://localhost:8000',
                'tag'        => 'PHP 8.2',
                'container'  => 'php_apache_server',
                'hosted_on'  => $DOCKER_BADGE,
            ],
            [
                'name'       => 'SSH — Arch Linux VM',
                'host'       => $GATEWAY,
                'port'       => 22,
                'url'        => '#',
                'tag'        => 'SSH :2222',
                'container'  => 'sshd (nativo)',
                'hosted_on'  => "{$osIcon} {$hostOS['name']} (nativo)",
            ],
        ]
    ],
];

// ── TCP check ────────────────────────────────────────────────
function checkPort(string $host, int $port, int $timeout = 2): array {
    if ($host === 'host-only') return ['online' => null, 'ms' => null];
    $t  = microtime(true);
    $fp = @fsockopen($host, $port, $errno, $errstr, $timeout);
    $ms = round((microtime(true) - $t) * 1000);
    if ($fp) { fclose($fp); return ['online' => true, 'ms' => $ms]; }
    return ['online' => false, 'ms' => null];
}

// Run all checks
$totalOn = 0; $totalSvc = 0;
foreach ($services as &$group) {
    foreach ($group['items'] as &$item) {
        $r = checkPort($item['host'], $item['port']);
        $item['online'] = $r['online'];
        $item['ms']     = $r['ms'];
        $totalSvc++;
        if ($r['online'] === true) $totalOn++;
    }
}
unset($group);
unset($item);

$checkedAt = date('H:i:s');
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="15">
    <title>Biomedical Hub — Estado de Servicios</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg:      #070b13;
            --bg2:     #0c1220;
            --card:    #0f1929;
            --accent:  #00d2c4;
            --accent2: #8c52ff;
            --green:   #10b981;
            --red:     #ef4444;
            --yellow:  #f59e0b;
            --blue:    #3b82f6;
            --muted:   #64748b;
            --border:  rgba(255,255,255,0.06);
            --text:    #f1f5f9;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

        /* Header */
        .hdr {
            background: linear-gradient(135deg,#0c1220,#0a1628);
            border-bottom: 1px solid var(--border);
            padding: 18px 36px;
            display: flex; align-items: center; justify-content: space-between;
            position: sticky; top: 0; z-index: 100;
        }
        .hdr h1 {
            font-size: 1.2rem; font-weight: 700;
            background: linear-gradient(90deg, var(--accent), var(--accent2));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .hdr p { font-size: .75rem; color: var(--muted); margin-top: 2px; }

        /* Env banner */
        .env-banner {
            display: flex; align-items: center; gap: 12px;
            background: var(--bg2); border: 1px solid rgba(0,210,196,.2);
            border-radius: 10px; padding: 10px 18px; margin: 20px 36px 0;
        }
        .env-icon { font-size: 1.6rem; }
        .env-info h2 { font-size: .85rem; font-weight: 600; color: var(--accent); }
        .env-info p  { font-size: .72rem; color: var(--muted); margin-top: 2px; font-family: 'JetBrains Mono', monospace; }
        .env-pills { display: flex; gap: 8px; margin-left: auto; flex-wrap: wrap; }
        .pill {
            font-size: .68rem; font-family: 'JetBrains Mono', monospace;
            background: rgba(255,255,255,.05); border: 1px solid var(--border);
            border-radius: 100px; padding: 3px 10px; color: var(--muted);
        }
        .pill.green { background: rgba(16,185,129,.12); border-color: rgba(16,185,129,.3); color: var(--green); }
        .pill.yellow{ background: rgba(245,158,11,.12); border-color: rgba(245,158,11,.3); color: var(--yellow); }

        /* Status pills */
        .hdr-right { display: flex; align-items: center; gap: 16px; }
        .badge {
            display: flex; align-items: center; gap: 8px;
            background: var(--card); border: 1px solid var(--border);
            border-radius: 100px; padding: 6px 14px;
        }
        .badge-n { font-size: 1.1rem; font-weight: 700; color: var(--green); }
        .badge-n.w { color: var(--yellow); }
        .badge-n.b { color: var(--red); }
        .badge-lbl { font-size: .78rem; color: var(--muted); }
        .pulse-wrap { display:flex;align-items:center;gap:6px;font-size:.72rem;color:var(--muted); }
        .pulse { width:7px;height:7px;background:var(--green);border-radius:50%;animation:blink 2s infinite; }
        @keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

        /* Main grid */
        .container { padding: 20px 36px 36px; max-width: 1500px; margin: 0 auto; }
        .group-section { margin-bottom: 30px; }
        .group-header { display:flex;align-items:center;gap:10px;margin-bottom:12px; }
        .group-title { font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.09em;color:var(--muted); }
        .divider { flex:1;height:1px;background:var(--border);margin-left:6px; }
        .g-count { font-size:.68rem;color:var(--muted);background:var(--bg2);border:1px solid var(--border);border-radius:100px;padding:2px 9px; }

        /* Cards */
        .grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px; }
        .card {
            position:relative;overflow:hidden;
            background:var(--card);border:1px solid var(--border);
            border-radius:12px;padding:14px 16px;
            display:flex;flex-direction:column;gap:10px;
            text-decoration:none;color:inherit;
            transition:transform .18s,border-color .18s;
        }
        .card:hover { transform:translateY(-2px);border-color:rgba(255,255,255,.12); }
        .card::before { content:'';position:absolute;inset:0;border-radius:12px;pointer-events:none; }
        .card.online::before  { background:rgba(16,185,129,.08); }
        .card.offline::before { background:rgba(239,68,68,.08); }
        .card.host::before    { background:rgba(245,158,11,.07); }

        /* Card top row */
        .card-top { display:flex;align-items:center;gap:12px; }
        .dot { width:10px;height:10px;border-radius:50%;flex-shrink:0; }
        .dot.online  { background:var(--green);box-shadow:0 0 8px var(--green);animation:pg 2.5s infinite; }
        .dot.offline { background:var(--red);  box-shadow:0 0 6px var(--red); }
        .dot.host    { background:var(--yellow);box-shadow:0 0 6px var(--yellow); }
        @keyframes pg{0%,100%{box-shadow:0 0 6px var(--green)}50%{box-shadow:0 0 14px var(--green)}}
        .card-name { font-size:.9rem;font-weight:600;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
        .status-lbl {
            font-size:.66rem;font-weight:600;padding:3px 9px;border-radius:100px;flex-shrink:0;
        }
        .status-lbl.online  { background:rgba(16,185,129,.15);color:var(--green); }
        .status-lbl.offline { background:rgba(239,68,68,.12); color:var(--red); }
        .status-lbl.host    { background:rgba(245,158,11,.12);color:var(--yellow); }

        /* Card meta row */
        .card-meta { display:flex;align-items:center;gap:7px;flex-wrap:wrap; }
        .tag {
            font-size:.63rem;font-family:'JetBrains Mono',monospace;
            background:rgba(255,255,255,.05);border:1px solid var(--border);
            border-radius:4px;padding:1px 7px;color:var(--muted);
        }
        .ms { font-size:.68rem;font-family:'JetBrains Mono',monospace; }
        .ms.ok   { color:var(--green); }
        .ms.fail { color:var(--red); }
        .ms.win  { color:var(--yellow); }

        /* Hosting badge */
        .host-badge {
            display:flex;align-items:center;gap:6px;
            background:rgba(255,255,255,.03);border:1px solid var(--border);
            border-radius:6px;padding:5px 9px;margin-top:2px;
        }
        .host-badge-icon { font-size:.8rem; }
        .host-badge-text { flex:1;min-width:0; }
        .host-badge-env {
            font-size:.67rem;font-weight:600;color:var(--accent);
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
        }
        .host-badge-ctn {
            font-size:.6rem;font-family:'JetBrains Mono',monospace;
            color:var(--muted);margin-top:1px;
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
        }
        .host-type-tag {
            font-size:.58rem;font-family:'JetBrains Mono',monospace;
            padding:2px 6px;border-radius:4px;flex-shrink:0;
        }
        .host-type-tag.docker  { background:rgba(0,210,196,.12);border:1px solid rgba(0,210,196,.25);color:var(--accent); }
        .host-type-tag.windows { background:rgba(59,130,246,.12);border:1px solid rgba(59,130,246,.25);color:var(--blue); }
        .host-type-tag.native  { background:rgba(140,82,255,.12);border:1px solid rgba(140,82,255,.25);color:var(--accent2); }

        footer {
            text-align:center;padding:20px;color:var(--muted);
            font-size:.72rem;border-top:1px solid var(--border);margin-top:10px;
        }
        footer a { color:var(--accent);text-decoration:none; }
        .legend { display:flex;justify-content:center;gap:18px;margin-top:8px;flex-wrap:wrap; }
        .leg-item { display:flex;align-items:center;gap:5px;font-size:.64rem; }

        @media(max-width:700px){
            .hdr{flex-direction:column;gap:12px;padding:14px 18px;}
            .container{padding:14px 18px 28px;}
            .env-banner{margin:14px 18px 0;flex-direction:column;align-items:flex-start;}
            .env-pills{margin-left:0;}
        }
    </style>
</head>
<body>

<header class="hdr">
    <div>
        <h1>⚕️ Biomedical Hub — Estado de Servicios</h1>
        <p>Verificación TCP interna · Docker network · Auto-detección de entorno</p>
    </div>
    <div class="hdr-right">
        <?php
            $r = $totalSvc > 0 ? $totalOn / $totalSvc : 0;
            $bc = $r >= 1 ? '' : ($r >= .7 ? 'w' : 'b');
        ?>
        <div class="badge">
            <span class="badge-n <?= $bc ?>"><?= $totalOn ?>/<?= $totalSvc ?></span>
            <span class="badge-lbl">docker online</span>
        </div>
        <div class="pulse-wrap">
            <span class="pulse"></span>
            <?= $checkedAt ?> · 15s
        </div>
    </div>
</header>

<!-- Environment Banner -->
<div class="env-banner">
    <div class="env-icon"><?= $osIcon ?></div>
    <div class="env-info">
        <h2>Entorno Docker detectado: <?= htmlspecialchars($hostOS['pretty']) ?></h2>
        <p><?= isset($hostOS['kernel']) ? htmlspecialchars(substr($hostOS['kernel'], 0, 80)) : 'Kernel info no disponible' ?></p>
    </div>
    <div class="env-pills">
        <span class="pill green">Docker activo</span>
        <span class="pill"><?= htmlspecialchars($hostOS['id']) ?></span>
        <?php if ($hostOS['version']): ?>
            <span class="pill"><?= htmlspecialchars($hostOS['version']) ?></span>
        <?php endif; ?>
        <span class="pill yellow">Check TCP server-side</span>
    </div>
</div>

<main class="container">
<?php foreach ($services as $group): ?>
    <section class="group-section">
        <div class="group-header">
            <span><?= $group['icon'] ?></span>
            <span class="group-title"><?= htmlspecialchars($group['group']) ?></span>
            <div class="divider"></div>
            <?php
                $gOn  = count(array_filter($group['items'], fn($i) => $i['online'] === true));
                $gTot = count($group['items']);
            ?>
            <span class="g-count"><?= $gOn ?>/<?= $gTot ?></span>
        </div>
        <div class="grid">
        <?php foreach ($group['items'] as $item):
            if ($item['online'] === null) {
                $cls = 'host'; $lbl = 'HOST-ONLY';
            } elseif ($item['online']) {
                $cls = 'online'; $lbl = 'ONLINE';
            } else {
                $cls = 'offline'; $lbl = 'OFFLINE';
            }

            // Determine host type for badge
            $hostedOn = $item['hosted_on'];
            if (str_contains($hostedOn, 'Docker')) {
                $typeTag = 'docker'; $typeLabel = 'Docker';
            } elseif (str_contains($hostedOn, 'Windows')) {
                $typeTag = 'windows'; $typeLabel = 'Windows';
            } else {
                $typeTag = 'native'; $typeLabel = 'Nativo';
            }
        ?>
            <a class="card <?= $cls ?>" href="<?= htmlspecialchars($item['url']) ?>" target="_blank">
                <!-- Top: dot + name + status -->
                <div class="card-top">
                    <span class="dot <?= $cls ?>"></span>
                    <span class="card-name"><?= htmlspecialchars($item['name']) ?></span>
                    <span class="status-lbl <?= $cls ?>"><?= $lbl ?></span>
                </div>

                <!-- Meta: tags + ms -->
                <div class="card-meta">
                    <span class="tag"><?= htmlspecialchars($item['tag']) ?></span>
                    <span class="tag">:<?= $item['port'] ?></span>
                    <?php if ($item['online'] === true): ?>
                        <span class="ms ok">⚡ <?= $item['ms'] ?>ms</span>
                    <?php elseif ($item['online'] === false): ?>
                        <span class="ms fail">sin respuesta</span>
                    <?php else: ?>
                        <span class="ms win">sólo desde Windows</span>
                    <?php endif; ?>
                </div>

                <!-- Hosting badge -->
                <div class="host-badge">
                    <span class="host-badge-icon"><?= str_contains($typeTag,'windows') ? '🪟' : (str_contains($typeTag,'native') ? '🐧' : '🐳') ?></span>
                    <div class="host-badge-text">
                        <div class="host-badge-env"><?= htmlspecialchars($hostedOn) ?></div>
                        <div class="host-badge-ctn">📦 <?= htmlspecialchars($item['container']) ?></div>
                    </div>
                    <span class="host-type-tag <?= $typeTag ?>"><?= $typeLabel ?></span>
                </div>
            </a>
        <?php endforeach; ?>
        </div>
    </section>
<?php endforeach; ?>
</main>

<footer>
    Verificación TCP server-side desde <code>php_apache_server</code> ·
    Entorno: <strong><?= htmlspecialchars($hostOS['pretty']) ?></strong> ·
    <a href="http://localhost:8085">← Homer Dashboard</a>
    <div class="legend">
        <span class="leg-item">🟢 ONLINE — puerto TCP respondiendo</span>
        <span class="leg-item">🔴 OFFLINE — sin respuesta en red Docker</span>
        <span class="leg-item">🟡 HOST-ONLY — servicio en Windows (accesible desde navegador)</span>
        <span class="leg-item">🐳 Docker · 🐧 Nativo · 🪟 Windows Host</span>
    </div>
</footer>

</body>
</html>
