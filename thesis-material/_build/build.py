#!/usr/bin/env python3
"""Schreibbaukasten aus dem unveränderten Stage-1-Audit erzeugen (nur Standardbibliothek)."""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / '_stage1'
LF = '\n'  # Zeilenenden unabhängig vom Betriebssystem
WATERMARK = 'Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.'
units = json.loads((AUDIT / 'inventory-merged.json').read_text(encoding='utf-8'))['units']
original_sources = json.loads((AUDIT / 'sources-merged.json').read_text(encoding='utf-8'))
overrides = json.loads((ROOT / '_build/source-overrides.json').read_text(encoding='utf-8'))
# Abgleich mit neueren integration-Entscheidungen: Notizen ergänzen die Aussagen, ersetzen sie nicht.
notes = json.loads((ROOT / '_build/integration-notes.json').read_text(encoding='utf-8'))
sources = {k: dict(v, **overrides.get(k, {})) for k, v in original_sources.items()}
by_id = {u['id']: u for u in units}
assert len(by_id) == len(units) == 350
stage1_before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in AUDIT.rglob('*') if p.is_file()}
replaced = collections.defaultdict(list)
for u in units:
    old_ids = u.get('supersedes', [])
    if isinstance(old_ids, str): old_ids = [old_ids]
    for old in old_ids:
        assert old in by_id and old != u['id']
        replaced[old].append(u['id'])
active = [u for u in units if u['id'] not in replaced]
# Notizen nur an sichtbaren Schreibbausteinen; ersetzte IDs erscheinen nicht in den Kapiteln.
assert set(notes['units']) <= {u['id'] for u in active}, set(notes['units']) - {u['id'] for u in active}

# Explizite Themenfolge; die Dateinummern entsprechen dem Schreibpfad.
chapters = [
 ('01-einleitung.md', 'Einleitung und Motivation', 'Ziel, Problem und Beitrag des Prototyps beschreiben.'),
 ('02-grundlagen-medizinisch.md', 'Medizinische Grundlagen', 'Herzzyklus → Herztöne → Herzgeräusche → Auskultationsbandbreite.'),
 ('03-grundlagen-technisch/01-akustik-bruststueck.md', 'Akustik und Bruststück', 'Schalldruck und Übertragung → Kopplung → Resonanzmodelle → Grenzen.'),
 ('03-grundlagen-technisch/02-mems-mikrofone.md', 'MEMS-Mikrofone', 'LFRO und Kennwerte → Schnittstellen und Bauteilvergleich → Grenzen der Entzerrung.'),
 ('03-grundlagen-technisch/03-i2s-audiopfad.md', 'I²S und digitaler Audiopfad', 'Digitale Audioübertragung → PDM/PCM → DMA → externe Ausgabe.'),
 ('03-grundlagen-technisch/04-dsp-filter.md', 'DSP und Filter', 'Filterwirkung → Hüllkurven und Spektralmerkmale → Rechenaufwand.'),
 ('03-grundlagen-technisch/05-bpm-erkennung.md', 'BPM-Erkennung', 'Zeitbezug der Herzfrequenz → Referenzintervalle → Grenzen der Schätzung.'),
 ('03-grundlagen-technisch/06-time-stretch.md', 'Time-Stretch und verlangsamte Wiedergabe', 'Resampling/TSM → SOLA/WSOLA → Phase-Vocoder → Artefakte und Startparameter.'),
 ('03-grundlagen-technisch/07-embedded-rtos-esp32.md', 'Embedded-System, RTOS und ESP32', 'Plattform und Treiber → Scheduling und Speicher → dokumentierte Grenzen.'),
 ('03-grundlagen-technisch/08-fhir-tls.md', 'FHIR und TLS', 'Observation und Kodierung → Patient/Zeitbezug → Transport und Zertifikatsprüfung.'),
 ('03-grundlagen-technisch/09-latenz.md', 'Latenz und Echtzeit', 'End-to-End-Begriff → kontextabhängige Wahrnehmung → vorläufige Entwicklungsziele.'),
 ('04-stand-der-technik.md', 'Stand der Technik', 'Veröffentlichte Verfahren, Geräte und Simulatoren mit dem Projektbedarf vergleichen.'),
 ('05-anforderungen.md', 'Anforderungen und Abgrenzung', 'Funktionsumfang → eigene Zielwerte → ausdrücklich ausgeschlossene Nachweise.'),
 ('06-systemarchitektur.md', 'Systemarchitektur', 'Bruststück und Hardware → Signalpfade → Bedienung → Tasks/Speicher → Netzwerk.'),
 ('07-implementierung.md', 'Implementierung', 'Dokumentierten Softwarestand mit Versions- und Verdrahtungsbezug beschreiben.'),
 ('08-evaluation/01-fragen-kriterien.md', 'Evaluation: Fragen und Annahmekriterien', 'Forschungsfragen → eigene Akzeptanzziele → Grenzen des Nachweises.'),
 ('08-evaluation/02-datensaetze-referenz.md', 'Evaluation: Datensätze und Referenzen', 'Daten/Lizenzen → Labels → Auswahl → unabhängige BPM-Referenz.'),
 ('08-evaluation/03-filtervergleich-statistik.md', 'Evaluation: Filtervergleich und Statistik', 'Vergleichsgrößen definieren → fairer Versuchsaufbau → gepaarte Auswertung.'),
 ('08-evaluation/04-bpm-validierung.md', 'Evaluation: BPM-Validierung', 'Referenz synchronisieren → Fehlermaße → eigene Toleranzen → Auswertung.'),
 ('08-evaluation/05-hoerstudie.md', 'Evaluation: Explorative Hörstudie', 'Pilotcharakter → Aufgaben → Stimuli/Randomisierung → Auswertung und Grenzen.'),
 ('08-evaluation/06-akustische-kette.md', 'Evaluation: Akustische Übertragungskette', 'Optionaler Messumfang → Koppler/Referenz → Signale → Unsicherheit. W1 zuerst klären.'),
 ('08-evaluation/07-firmware-funktion-ressourcen.md', 'Evaluation: Firmware, Funktion und Ressourcen', 'Prüfverfahren → Build/Host-Nachweise → historische Hardwarebefunde → offene Integration.'),
 ('09-ethik-datenschutz-regulatorik.md', 'Ethik, Datenschutz und Regulatorik', 'Zuständigkeit → Einwilligung → Datenminimierung → Transport → Grenzen der Konformität.'),
 ('10-diskussion-ausblick.md', 'Diskussion und Ausblick', 'Widersprüche und Einschränkungen → Übertragbarkeit → begründete nächste Schritte.'),
 ('11-formales-projektmanagement.md', 'Formales und Projektmanagement', 'Anmeldung und verbindliche Frist → Arbeitsumfang → Dokumentation der Recherche.'),
]
files = [c[0] for c in chapters]
route = {}
def assign(file_index, ids):
    for token in ids.split():
        match = re.fullmatch(r'([UABC])(\d+)-(?:[UABC])?(\d+)', token)
        expanded = [f'{match[1]}{n:03d}' for n in range(int(match[2]), int(match[3])+1)] if match else [token]
        for uid in expanded:
            assert uid in by_id, uid
            route[uid] = files[file_index]

# Grundzuordnung übernimmt den klassifizierten Kapitelbezug; Themen werden darunter kuratiert.
base = {'Einleitung/Motivation':0, 'Grundlagen (medizinisch: Herztöne, Murmurs, Auskultation)':1,
 'Stand der Technik':11, 'Anforderungen':12, 'Systemarchitektur':13, 'Implementierung':14,
 'Evaluation/Methodik':15, 'Ethik/Datenschutz/Regulatorik':22, 'Diskussion/Ausblick':23,
 'Projektmanagement/Formales':24}
for u in units:
    if u['chapter'] in base: route[u['id']] = files[base[u['chapter']]]
assign(1, 'U073 U074 A014-A016 A060')
assign(2, 'U059 B042-B047 B068 B070-B072')
assign(3, 'U061 B048-B055 B078 B080')
assign(4, 'C008-C012')
assign(5, 'A005-A008 C016 C017 C019')
assign(6, 'A046')
assign(7, 'U051 A058 A059 A061-A073')
assign(8, 'C014')
assign(9, 'U068 C029 C030 C032-C034 C038 C040 C041')
assign(10, 'C001 C006 C007')
assign(15, 'U004 U005 U013-U015 U019 U026 U089 U109-U112 U119 U123 U125')
assign(16, 'U017 U044 U045 U122 A021-A031 A040-A045')
assign(17, 'U041 U042 U049 U050 U121 A001-A004 A009-A013 A017-A020')
assign(18, 'U018 U047 U048 U124 A047-A057 C020-C022')
assign(19, 'U006 U016 U021 U053-U055 B001-B021 B076 B077 B081-B086')
assign(20, 'U063 A032-A034 B056-B067 B069 B073 B074')
assign(21, 'U090-U098 U108 U113-U118 U126-U130 U132 U133 A074-A076 C015 C024 C042')
assign(11, 'A035-A039 B040 B041')
assign(13, 'A065 A077 B036-B039')
assign(23, 'A078 A079')
assert set(route) == set(by_id), f'Ohne Thema: {set(by_id)-set(route)}'

# Unterthemen geben auch großen Kapiteln eine nachvollziehbare Schreibreihenfolge.
def topic(u):
    file = route[u['id']]
    t = u['statement'].lower()
    if file == files[13]:
        if re.search(r'bruststück|membran|mikrofon|kopplung|schlauch', t): return (0,'Bruststück, Mikrofon und Kopplung')
        if re.search(r'schalter|sp3t|gpio|potentiometer|display|verdraht|pinzuordnung', t): return (2,'Bedienung, Pins und Verdrahtung')
        if re.search(r'fhir|tls|https|sntp|root-ca|zertifikat', t): return (4,'Netzwerk- und Übertragungspfad')
        if re.search(r'rtos|zephyr|esp-idf|rechenbudget|dma|psram|sram|cpu|thread|task',t): return (3,'Plattform, Tasks und Ressourcen')
        return (1,'Audiohardware und getrennte Signalpfade')
    if file == files[21]:
        if u['type'] == 'measurement': return (3,'Dokumentierte Befunde mit Datum und Versionsbezug')
        if re.search(r'host|build|qc|ci|baseline|schema',t): return (1,'Build-, Host- und QC-Nachweise')
        if re.search(r'tls|heap|ressource|time-stretch|cpu|latenz',t): return (2,'Laufzeit, Speicher und Netzwerkprüfung')
        return (0,'Funktionstest und physische Annahmekriterien')
    if file == files[19]:
        if re.search(r'binomial|statisti|p-werte|wilcoxon|effektgröße|trefferquote|rohdat|konfidenz|mixed-effects|17/20',t): return (3,'Auswertung und Unsicherheit')
        if re.search(r'stimul|verblind|randomis|übung|übungs|pausen|sitzung|lautheit|alter,|hörscreen',t): return (2,'Stimuli und Durchführung')
        if re.search(r'abx|2afc|within-subject|diskrimin|detektionsstufe',t): return (1,'Aufgaben und Versuchsdesign')
        return (0,'Ziel, Stichprobe und Aussagegrenzen')
    if file == files[22]:
        if re.search(r'tls|https|zertifikat',t): return (3,'Sicherer Transport')
        if re.search(r'einwillig|teilnehmerinfo|freiwillig',t): return (1,'Einwilligung und Information')
        if re.search(r'dsgvo|anonym|pseudonym|daten|physionet|lizenz|lösch',t): return (2,'Datenschutz und Nachnutzung')
        return (0,'Ethikzuständigkeit und regulatorische Abgrenzung')
    if file == files[24]:
        if re.search(r'recherche|runs.json|prompt|forschungslog|readme|stand 2026',t): return (3,'Recherche- und Dokumentationsstand')
        if re.search(r'320|aufwand|phase 1|personenwoche',t): return (2,'Aufwand und Zeitbudget')
        if re.search(r'titel|untertitel',t): return (1,'Titel und fakultätsspezifische Vorgaben')
        return (0,'Anmeldung, Abgabe und geltende Regeln')
    return (0,'Schreibbausteine')

def role(u):
    # Reihenfolge innerhalb jedes Themas: Definition → Mechanismus → Werte → Folgerung.
    typ = u['type']
    if typ == 'definition': return 0
    if typ in ('fact','formal-rule'): return 1
    if typ in ('parameter','measurement'): return 2
    return 3
role_labels = ['Begriffe und Definitionen','Mechanismen und Zusammenhänge','Werte und dokumentierte Befunde','Folgerungen, Entwurfsentscheidungen und Grenzen']
status_labels = {'assumption':'ANNAHME', 'open':'OFFEN', 'contradicted':'WIDERSPRUCH'}

def marker(u):
    typ, t = u['type'], u['statement'].lower()
    if typ == 'contradiction': return 'WIDERSPRUCH'
    if typ == 'open-question': return 'OFFENE FRAGE'
    if typ == 'decision': return 'EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG'
    if typ == 'requirement': return 'EIGENE ANFORDERUNG'
    if typ == 'alternative-rejected': return 'VERWORFENE ALTERNATIVE'
    if typ == 'risk': return 'RISIKO / EINORDNUNG'
    if typ == 'method': return 'METHODENVORSCHLAG' if re.search(r'empfiehlt|schlägt|soll|vorgeschlagen',t) else 'METHODE / PRÜFVERFAHREN'
    if typ == 'measurement': return 'LITERATURMESSUNG / BENCHMARK' if u['needs_citation'] else 'EIGENER DOKUMENTIERTER BEFUND'
    if typ == 'parameter':
        if not u['needs_citation'] or re.search(r'ziel|startparameter|startwerte|schätz|beispielparameter|pilotkonfiguration|listet wsola|nennt ess-einstellungen|pro trial|pro person', t):
            return 'EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG'
        return 'LITERATUR- / HERSTELLERWERT'
    return 'LITERATURFAKT / REGEL' if u['needs_citation'] else 'PROJEKTDOKUMENTATION'

# Markdown-Links immer mit '/' erzeugen, damit Windows- und Linux-Läufe identische Dateien schreiben.
def posix_relpath(target, start):
    return os.path.relpath(target, start).replace(os.sep, '/')

def relative(src, dest):
    return quote(posix_relpath(ROOT / dest, (ROOT / src).parent), safe='/.-_')

def heading_anchors(text):
    # Gleiche Slug-Regel wie Development/system/testing/ci/validate_docs.py.
    found, counts = set(), {}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*\s*$', re.sub(r'```.*?```', '', text, flags=re.DOTALL), re.MULTILINE):
        slug = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        found.add(slug if not counts.get(slug) else f'{slug}-{counts[slug]}')
        counts[slug] = counts.get(slug, 0) + 1
    return found

checked_refs = set()
def repo_link(title, path, anchor, src):
    target = ROOT.parent / path
    assert target.is_file(), f'integration-Verweis fehlt: {path}'
    if anchor:
        assert anchor in heading_anchors(target.read_text(encoding='utf-8')), f'Anker fehlt: {path}#{anchor}'
    checked_refs.add(path + ('#' + anchor if anchor else ''))
    return f'[{title}]({quote(posix_relpath(target, (ROOT / src).parent), safe="/.-_")}' + (f'#{anchor}' if anchor else '') + ')'

def render_note(note, src):
    refs = ', '.join(repo_link(t, p, a, src) for t, p, a in note['refs'])
    return f'> **{note["label"]} (Stand integration, {notes["stand"]}):** {note["changed"]} Aktuell: {note["current"]} – siehe {refs}.'

def unit_link(uid, src):
    target = replaced.get(uid, [uid])[0]
    return f'[{uid}]({relative(src,route[target])}#{target.lower()})'

def source_link(key, src): return f'[{key}]({relative(src,"quellen.md")}#{key})'

missing_origins=set()
def origins(u, src):
    result=[]
    for origin in [part.strip() for raw in u['origin'] for part in raw.split(';')]:
        m=re.match(r'^(.*?):([\d,\-]+)$',origin)
        path,line=(m[1],m[2]) if m else (origin,None)
        anchor='#L'+re.split(r'[-,]',line)[0] if line else ''
        if not (ROOT.parent/path).exists():
            # Herkunftsdatei existiert auf integration nicht mehr: historische Fassung verlinken statt abzubrechen.
            moved=notes['relocated_origins'].get(path)
            if moved:
                cur=moved['current']
                result.append(f'[{origin}]({notes["repository_url"]}/blob/{moved["commit"]}/{quote(path,safe="/.-_")}{"?plain=1" if anchor and path.endswith(".md") else ""}{anchor}) (**Herkunft verschoben:** {moved["note"]} Aktuell: {repo_link(cur[0],cur[1],cur[2],src)})')
            else:
                missing_origins.add(path)
                result.append(f'`{origin}` (**Herkunft nicht mehr im Repository**; in Git-Historie suchen)')
            continue
        href=quote(posix_relpath(ROOT.parent/path,(ROOT/src).parent),safe='/.-_')
        result.append(f'[{origin}]({href}{anchor})')
    return '; '.join(result)

def flags(s):
    result=[]
    if 'broken' in s.get('link_check','').lower(): result.append('**LINK DEFEKT**')
    if s.get('paywalled') is True: result.append('🔒 Volltext kostenpflichtig')
    elif s.get('paywalled') not in (False,None): result.append('🔒 Volltextzugang prüfen: '+str(s['paywalled']))
    return ' · '.join(result)

def short_ref(key):
    s=sources[key]; ref=s['reference']
    first=ref.split('. ')[0]
    year=re.search(r'\((\d{4})\)',ref)
    return (first[:52]+(' '+year[1] if year else '')) + f' · {key}'

def citation(c, src):
    key=c['key']; s=sources[key]
    url=s.get('url') if key in overrides else c.get('link')
    if not str(url).startswith(('https://','http://')): url=s.get('url')
    if not str(url).startswith(('https://','http://')): url=relative(src,'quellen.md')+'#'+key
    page=str(c.get('page','unverified'))
    if 'unverified' in page.lower():
        hint=c.get('page_hint')
        place='Seite prüfen'+(f' (Hinweis: {hint})' if hint else (f' (übernommene Angabe: {page})' if page!='unverified' else ''))
    elif re.fullmatch(r'\d+(?:[–-]\d+)?',page): place='S. '+page
    else: place='Fundstelle: '+page+' (aus Stage 1; am Original prüfen)'
    return f'[{short_ref(key)}]({url}) — {place}'+(' · '+flags(s) if flags(s) else '')

def render_unit(u, src):
    uid=u['id']; tags=[marker(u)]
    if u['status']!='confirmed':tags.append(status_labels[u['status']])
    if u.get('sources_incomplete'):tags.append('QUELLENSET UNVOLLSTÄNDIG')
    olds=u.get('supersedes',[])
    if isinstance(olds,str): olds=[olds]
    tail=' · ersetzt '+', '.join(olds) if olds else ''
    lines=[f'<a id="{uid.lower()}"></a>',f'**{uid} · {" · ".join(tags)}{tail}**', '',u['statement'],'']
    if uid in notes['units']: lines+=[render_note(notes['units'][uid],src),'']
    lines.append(f'**Ursprung:** {origins(u,src)}')
    if u.get('chapter_secondary'): lines.append('**Weiterer Kapitelbezug:** '+str(u['chapter_secondary']))
    lines.append('**Belege:** '+('; '.join(citation(c,src) for c in u.get('sources',[])) or 'Keine externen Belege im Inventar; Projektursprung verwenden.'))
    if u.get('removed'):lines.append('**Audit:** verworfene Quellen siehe '+relative(src,'_stage1/inventory-merged.json')+' (Feld `removed`).')
    if u['status']=='contradicted':lines.append(f'**Vor Verwendung klären:** [Widersprüche]({relative(src,"offene-punkte.md")}#widersprueche).')
    return '\n'.join(lines)+'\n\n'

groups=collections.defaultdict(list)
for u in active: groups[route[u['id']]].append(u)
outputs={}
for path,title,intro in chapters:
    us=sorted(groups[path],key=lambda u:(topic(u)[0],role(u),u['statement'].casefold()))
    text=f'# {title}\n\n[Zum Einstieg]({relative(path,"README.md")}) · [Offene Punkte]({relative(path,"offene-punkte.md")})\n\n{intro}\n\n**{len(us)} aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.\n\n'
    if path.startswith('03-') or path.startswith('02-'):
        text+='**Schreibhinweis:** Literaturgrundlagen erklären das Verfahren. Zielwerte, Architekturentscheidungen und Berichtsempfehlungen als solche benennen und später in Anforderungen/Methodik begründen.\n\n'
    if path==files[2]: text+='**Achtung:** Helmholtz-Abschätzung und gekoppeltes Bruststückmodell widersprechen sich; [B075]('+relative(path,files[23])+'#b075) vor Zahlenübernahme lesen.\n\n'
    if path==files[16]: text+='**Achtung:** CirCor-Aufnahmenzahl 5.272/5.282 ist ungeklärt; [A021](#a021) sichtbar stehen lassen.\n\n'
    if path==files[8]: text+='**Materiallücke:** Das Inventar liefert keine zusammenhängende Einführung in RTOS, Threadprioritäten und Zephyr-Scheduling. Die ESP-IDF-Empfehlung in der Architektur ist historischer Recherchekontext; der dokumentierte Prototyp nutzt Zephyr. Grundlagen ergänzen und am tatsächlich verwendeten Stand belegen.\n\n'
    last_topic=last_role=None
    for u in us:
        top=topic(u)
        if top!=last_topic:
            text+=f'## {top[1]}\n\n';last_topic=top;last_role=None
        if role(u)!=last_role:
            text+=f'### {role_labels[role(u)]}\n\n';last_role=role(u)
        text+=render_unit(u,path)
    outputs[path]=text.rstrip('\n')+'\n'

# Themenweise Bibliografie, Quellen-Verwendungsnachweis auch für ersetzte Einheiten.
usage=collections.defaultdict(list)
for u in units:
    for c in u.get('sources',[]):
        assert c['key'] in sources, c['key']
        if u['id'] not in usage[c['key']]: usage[c['key']].append(u['id'])
def source_topic(key):
    if key.startswith('tha_'):return 'Formales und Hochschule'
    if re.search(r'gdpr|gehba|ethic|anonym|pseudonym|dua|health_data',key):return 'Ethik, Datenschutz und Nachnutzung'
    if re.search(r'fhir|loinc',key):return 'FHIR und Interoperabilität'
    if key.startswith(('esp','zephyr')):return 'Embedded, Audio-Treiber und TLS'
    if re.search(r'mems|datasheet|knowles|ics4|im68|im69|mic_|ecm_',key):return 'Mikrofone und Herstellerunterlagen'
    if re.search(r'latency|aes_|wang_|sharma_|rhythm_',key):return 'Latenz und Wahrnehmung'
    if re.search(r'wsola|tsm|vocoder',key):return 'Time-Stretch'
    if re.search(r'pilot|2afc|abx|auscultation_test|agreement',key):return 'Hörstudie und Pilotmethodik'
    if re.search(r'bland|ec13|iec60601|hr_accuracy|heart_rate_validation',key):return 'BPM-Validierung und EKG-Monitornormen'
    if re.search(r'circor|physionet|challenge|database',key):return 'Datensätze und Referenzlabels'
    if re.search(r'stethoscope|acoustic|helmholtz|goh_|farina|ciric|iec60|iec61',key):return 'Akustik, Bruststück und Messmethoden'
    return 'Herzschall, Filter und Signalanalyse'
bib_text='# Quellenverzeichnis und Fundstellen\n\n[Zum Einstieg](README.md) · [Linkkorrekturen](linkkorrekturen.md) · [BibTeX](quellen.bib)\n\n103 Quellenschlüssel aus Stage 1. Doppelte Werke unter verschiedenen Schlüsseln bleiben für die Rückverfolgung erhalten. Die Zuordnung ist thematisch; alle zitierenden IDs werden genannt, auch ersetzte. „ok“ bezeichnet Linkzugang, nicht die Tragfähigkeit jeder Aussage. Seitenangaben sind getrennt zu prüfen.\n\n**BibTeX:** Für vier neu geprüfte Einträge stehen belegte Metadaten bereit. Die übrigen Minimal-Einträge enthalten nur die in Stage 1 überprüfte URL, wenn sie dort als erreichbar markiert ist, und eine als unsicher gekennzeichnete Arbeitsnotiz. Autoren, Titel, Jahre und DOIs werden dort nicht aus Freitext erraten. Vor der finalen Abgabe Originalmetadaten importieren.\n\n'
for category in sorted({source_topic(k) for k in sources}):
    bib_text+=f'## {category}\n\n'
    for key in sorted(k for k in sources if source_topic(k)==category):
        s=sources[key]
        bib_text+=f'<a id="{key}"></a>\n### {key}\n\n{s["reference"]}\n\n'
        bib_text+=f'**Linkstatus:** {s.get("link_check","nicht geprüft")}'+(' · '+flags(s) if flags(s) else '')+'\n\n'
        bib_text+=f'**Fundstelle:** [Quelle öffnen]({s.get("url")})' if str(s.get('url')).startswith(('https://','http://')) else '**Fundstelle:** URL ungeprüft / fehlt; Originalquelle beschaffen.'
        if s.get('doi') and s['doi']!='unverified':bib_text+=f' · DOI aus Arbeitsdatensatz: [{s["doi"]}]({s["doi"]})'
        bib_text+='\n\n**Prüfnachweis Stage 1:** '+s.get('verified','keiner')+'\n\n'
        if key in overrides:bib_text+='**Korrektur Stage 2:** '+overrides[key]['fix_reason']+'\n\n'
        if key=='pilot_guidelines':bib_text+='**METADATENKONFLIKT:** Der verlinkte PMC-Text gehört zu Teresi et al. (2022), Medical Care 60(1), 95–103, DOI 10.1097/MLR.0000000000001664. Der Ausgangseintrag nennt Leon (2011). Keine automatische Ersetzung: erst klären, welches Werk die Aussagen tatsächlich belegt.\n\n'
        bib_text+='**Zitiert von:** '+(', '.join(unit_link(uid,'quellen.md')+(' (ersetzt)' if uid in replaced else '') for uid in usage[key]) or 'Keine Einheit im Inventar.')+'\n\n'
outputs['quellen.md']=bib_text.rstrip('\n')+'\n'

def bib_escape(value):
    return str(value).replace('\\',r'\textbackslash{}').replace('&',r'\&').replace('%',r'\%').replace('#',r'\#').replace('_',r'\_')
bib=['% '+WATERMARK, '% Minimaldatensatz: Nicht belegte bibliografische Felder fehlen absichtlich.','']
for key,s in sources.items():
    fields=dict(s.get('bib',{}))
    if (key in overrides or s.get('link_check','').startswith('ok')) and str(s.get('url')).startswith(('https://','http://')):fields['url']=s['url']
    if key in overrides:
        fields['note']='Metadaten anhand der Primärfundstelle geprüft am 2026-10-05. Zitierte Einzelseiten und Aussagepassung separat prüfen. '+s['fix_reason']
    else:
        fields['note']='UNSICHERER MINIMALEINTRAG. Bibliografische Felder vor Verwendung am Original ergänzen. Referenztext aus Stage 1, nicht als Feldmetadaten verifiziert: '+s['reference']+' Linkstatus: '+s.get('link_check','nicht geprüft')
    bib.append('@misc{'+key+',\n'+',\n'.join('  '+k+' = {'+(str(v) if k in ('url','doi','author') else bib_escape(v))+'}' for k,v in fields.items())+'\n}\n')
outputs['quellen.bib']='\n'.join(bib)

broken_before={k for k,s in original_sources.items() if 'broken' in s.get('link_check','')}
broken_after={k for k,s in sources.items() if 'broken' in s.get('link_check','')}
fixes='# Linkkorrekturen und Suchprotokoll\n\n[Zum Einstieg](README.md)\n\nPrüfdatum: 05.10.2026. Änderungen liegen ausschließlich in [_build/source-overrides.json](_build/source-overrides.json); Stage 1 bleibt unverändert. Direkte HTTP-Proben: [_build/link-probes.json](_build/link-probes.json). Ein Suchtreffer allein genügt nicht zum Reparieren eines Links. Keine Seitenzahlen wurden neu festgelegt.\n\n## Verifiziert korrigiert\n\n'
for key,v in overrides.items():
    fixes+=f'### {key}\n\n{v["fix_reason"]}\n\n**Vorher:** {original_sources[key]["url"]}; DOI: {original_sources[key].get("doi","—")}\n\n**Jetzt:** [Fundstelle]({v["url"]}) · {v["link_check"]}\n\n**Identitätsnachweise:** '+', '.join(f'[Primärquelle {i+1}]({url})' for i,url in enumerate(v['evidence']))+'\n\n'
fixes+='## Unrepariert: sichtbar defekt\n\n'
reasons={
 'pilot_guidelines':'Titel gefunden, aber Werkidentität widersprüchlich (Leon 2011 versus Teresi 2022). Korrekturkandidat DOI 10.1097/MLR.0000000000001664; direkter Abruf HTTP 403. Aussagepassung zum PMC-Artikel prüfen, bevor Metadaten ersetzt werden.',
 'aes_lester_boley_2007':'Gleicher AES-Treffer gefunden; direkter Abruf endet mit Timeout bzw. Werkzeugfehler. Kein sicher funktionierender Ersatz.',
 'ecm_datasheet_im69d130':'Hersteller-PDF und älterer dgdl-Link gefunden, beide direkt nicht erreichbar (404). Produktseite ist kein Ersatz für dieselbe Datenblattfassung.',
 'ics40180_datasheet':'Herstellerkandidat DS-000021-v1.22.pdf aus bibliografischem Verweis geprüft; HTTP 404. Keine gesicherte Herstellerfassung erreichbar.',
 'tha_elektrotechnik_duration':'Passenden offiziellen PDF-Suchtreffer gefunden; direkter Abruf HTTP 404. Kein verifiziert erreichbarer Ersatz.',
}
for key in sorted(broken_after):
    reason=reasons.get(key,'THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.')
    fixes+=f'- {source_link(key,"linkkorrekturen.md")}: **LINK DEFEKT**. {reason}\n'
outputs['linkkorrekturen.md']=fixes+'\n'+WATERMARK+'\n'

# Jede Audit-ID ist über diesen Index zu ihrer aktiven Schreibstelle auffindbar.
index='# Einheitenindex\n\n[Zum Einstieg](README.md)\n\n350 Audit-IDs; aktive Aussagen erscheinen genau einmal in den Kapiteldateien. Ersetzte Aussagen werden nicht nochmals als aktueller Schreibbaustein gezeigt. Ihr Original bleibt im Audit erhalten.\n\n| ID | Schreibstelle | Typ / Status | Ersatz |\n|---|---|---|---|\n'
for u in units:
    uid=u['id']
    index+=f'| {uid} | {unit_link(uid,"einheitenindex.md")} | {u["type"]} / {u["status"]} | '+(', '.join(unit_link(n,'einheitenindex.md') for n in replaced[uid]) if uid in replaced else '—')+' |\n'
outputs['einheitenindex.md']=index

open_text='# Offene Punkte und Entscheidungen\n\n[Zum Einstieg](README.md) · [Quellen](quellen.md)\n\nBearbeitungsreihenfolge: Widersprüche vor Zahlenübernahme; Studien-/Hardwarefragen vor Versuchsbeginn; Quellen und Seiten spätestens vor finaler Zitierung. „confirmed“ im Audit bedeutet dokumentiert, nicht unabhängig bewiesen.\n\n<a id="widersprueche"></a>\n## Widersprüche — zuerst klären\n\n'
actions={
 'U037':'Mit dem Betreuer festlegen, ob Q1/AP 2.2 entfällt, qualitativ umformuliert oder mit Minimalmessung bearbeitet wird; Aufgabenbeschreibung, Methodik und Fazit angleichen. Playback prüft die reale Bruststückkopplung nicht.',
 'U039':'Schalter 1/2 verbindlich Filter/Geschwindigkeit zuordnen; Schaltplan, GPIO-Tabelle, Firmware und Testprotokoll abgleichen. Spätere Rev-A-Zuordnung nicht mit einem physischen Abnahmenachweis gleichsetzen.',
 'A021':'Gewählte CirCor-Version festhalten, Metadaten und heruntergeladenes Manifest zählen; 5.272 versus 5.282 mit Bezugsgröße (Personen/Aufnahmen/Subset) erklären.',
 'B075':'Geltungsbereich des Helmholtz-Modells gegen das gekoppelte Modell prüfen. 21-ml-/20-Hz-Abschätzung erst nach Plausibilitätsrechnung und Quellenprüfung verwenden; keine reale Kopplungsleistung daraus behaupten.',
 'B079':'Exakte Knowles-Modellnummer/Revision und LFRO-Definition im Original prüfen; 30 versus 35 Hz in der Vergleichstabelle auflösen.',
}
for u in units:
    if u['status']=='contradicted':
        note=render_note(notes['units'][u['id']],'offene-punkte.md')+'\n\n' if u['id'] in notes['units'] else ''
        open_text+=f'### {u["id"]}\n\n{u["statement"]}\n\n{note}**Nico:** {actions.get(u["id"],"Originaldokumente abgleichen und eine begründete Fassung festlegen.")}\n\n**Schreibstelle:** {unit_link(u["id"],"offene-punkte.md")}\n\n'
open_text+='## Weitere Konflikte und Nachweisgrenzen\n\n'
for text,ids,*conflict in [
 ('Abgabe laut Nico: **11.01.2027**. „Ende Januar“ und verschiedene fakultätsspezifische Bearbeitungsfristen bleiben historischer Kontext. Verbindlichen DMS-Termin und zuständige SPO/APO abgleichen.', ['U033','C045','C049','C051']),
 ('Prototyp nutzt ESP32/Zephyr; ESP-IDF-Favorisierung ist ein historischer Recherchevorschlag. Die tatsächlich getroffene Frameworkentscheidung und deren Begründung dokumentieren.', ['U028','U035','C013','U085'], 'framework'),
 ('Filter 40–800 Hz / 25–150 Hz, Live-Latenz <30 ms bzw. ≤10/≤5 ms und BPM-Grenzen sind vorläufige Entwicklungsziele. Eine gemeinsame Anforderungsversion und Messmethode festlegen.', ['U027','U102','U110','C001','A056','A057'], 'targets'),
 ('10–40-ms-DMA-Startwerte passen nicht ohne Prüfung zum ≤10-ms-End-to-End-Ziel. Tatsächliche Blocklatenz, Wandler- und Schedulinganteile am Prototyp messen.', ['C027','C001','U101'], 'dma'),
 ('Builds und Hosttests ersetzen keine integrierte Hardwareevaluation. Physische Tests am dokumentierten Firmware-Commit nachholen; Verdrahtungsbestätigung separat ausweisen.', ['U119','U125','U129','U130','U131']),
 ('Pilotstudienquelle: Leon-/Teresi-Metadatenkonflikt klären. Zusätzlich FDA-Publikationsjahr 1998 statt 2023 und EC13-1992-Bezug in der reparierten FDA-Fassung beachten.', ['B001','B016','A052']),
]:
    open_text+='- **Nico:** '+text+' Bezüge: '+', '.join(unit_link(i,'offene-punkte.md') for i in ids)+'.\n'
    if conflict:open_text+='\n  '+render_note(notes['conflicts'][conflict[0]],'offene-punkte.md')+'\n\n'
open_text+='\n<a id="integration-abgleich"></a>\n## Abgleich mit integration — nicht eindeutig entschieden\n\n'
open_text+=f'Stand integration {notes["stand"]} ({notes["integration_commit"]}). Diese Punkte wurden nicht als überholt markiert, weil kein neueres Dokument sie eindeutig entscheidet. Eindeutig überholte Aussagen tragen in den Kapiteldateien einen „Überholt“-Hinweis; Übersicht in [README](README.md#abgleich-mit-integration).\n\n'
for q in notes['open_questions']:
    open_text+='- **Nico:** '+q['text']+' Bezüge: '+', '.join(unit_link(i,'offene-punkte.md') for i in q['ids'])+'; '+', '.join(repo_link(t,p,a,'offene-punkte.md') for t,p,a in q['refs'])+'.\n'
open_text+='- **Nico:** Zitierte QC-Berichte (`QC-EVALUATION.md`, `qc-eval-results.json`) sind seit 89ca8b1 nicht mehr eingecheckt, sondern werden nach `artifacts/qc/` erzeugt. Die Herkunftslinks zeigen auf die historische Fassung in Git; für die Thesis entscheiden, ob der historische Bericht vom 24.09. oder ein neu erzeugter, datierter Bericht zitiert wird. Bezüge: '+', '.join(unit_link(i,'offene-punkte.md') for i in ('U091','U092','U097'))+'.\n'
open_text+='\n## Offene Fragen, Annahmen und Risiken\n\n'
for u in active:
    if u['type'] not in ('open-question','risk') and u['status'] not in ('open','assumption'):continue
    task='Antwort festlegen und im Projektursprung dokumentieren.' if u['type']=='open-question' else 'Geltungsbereich und Nachweis prüfen; bei einem Projektziel Entscheidung samt Akzeptanzkriterium dokumentieren.'
    if u['type']=='risk':task='Eintrittsbedingung und Auswirkung prüfen; Maßnahme oder begründete Begrenzung dokumentieren.'
    open_text+=f'- **{unit_link(u["id"],"offene-punkte.md")} · {u["status"]}:** {u["statement"]} **Nico:** {task}\n'
open_text+='\n## Unvollständige Quellensets\n\n45 Flags aus Stage 1; mehrere Quellen sind kein automatischer Qualitätsnachweis. Passende Primärbelege und konkrete Fundstellen prüfen; irrelevante Belege streichen. Flags ersetzter Einheiten bleiben als Audit-Hinweis, ohne sie automatisch auf den Ersatz zu übertragen.\n\n'
for u in units:
    if u.get('sources_incomplete'):
        open_text+=f'- {unit_link(u["id"],"offene-punkte.md")}'+(' (ersetzt; ursprüngliches Flag)' if u['id'] in replaced else '')+f': {len(u.get("sources",[]))} Belege. **Nico:** Aussage gegen passende Originalquellen prüfen; Lücke schließen oder Anspruch begrenzen.\n'
open_text+='\n## Ungeprüfte Seiten und Fundstellen\n\nDie 328 expliziten `page: unverified`-Verweise sind keine gesicherten Seitenangaben. Auch übernommene Abschnitts-/Tabellenhinweise am Original prüfen. Die folgende Liste umfasst zusätzlich Angaben, die „unverified“ nur als Teiltext enthalten.\n\n'
for u in units:
    refs=[c for c in u.get('sources',[]) if 'unverified' in str(c.get('page','unverified')).lower()]
    if refs:open_text+=f'- {unit_link(u["id"],"offene-punkte.md")}'+(' (ersetzt)' if u['id'] in replaced else '')+': '+', '.join(source_link(c['key'],'offene-punkte.md')+(f' — Hinweis: {c["page_hint"]}' if c.get('page_hint') else '') for c in refs)+'. **Nico:** Original öffnen, Aussagepassung und konkrete Seite/Abschnitt eintragen.\n'
open_text+='\n## Defekte Links und Quellenidentität\n\nVier Reparaturen sind in [linkkorrekturen.md](linkkorrekturen.md) belegt. Elf Ausgangseinträge bleiben defekt.\n\n'
for key in sorted(broken_after):
    open_text+=f'- {source_link(key,"offene-punkte.md")}: {sources[key]["link_check"]}. Betroffen: '+', '.join(unit_link(uid,'offene-punkte.md') for uid in usage[key])+'. **Nico:** identisches Werk über Originalanbieter/Hochschulbibliothek beschaffen; Metadaten und Fundstelle bestätigen.\n'
outputs['offene-punkte.md']=open_text

stats={'audit_units':len(units),'active_units':len(active),'superseded_ids':len(replaced),
 'superseding_units':sum(bool(u.get('supersedes')) for u in units),
 'citation_units':sum(u['needs_citation'] for u in units),
 'citation_units_with_at_least_three_sources':sum(u['needs_citation'] and len(u.get('sources',[]))>=3 for u in units),
 'incomplete_source_sets':sum(bool(u.get('sources_incomplete')) for u in units),
 'source_references':sum(len(u.get('sources',[])) for u in units),
 'unverified_pages_exact':sum(c.get('page')=='unverified' for u in units for c in u.get('sources',[])),
 'broken_entries_before':len(broken_before),'broken_entries_after':len(broken_after),
 'broken_affected_units_before':sum(any(c['key'] in broken_before for c in u.get('sources',[])) for u in units),
 'broken_affected_units_after':sum(any(c['key'] in broken_after for c in u.get('sources',[])) for u in units),
 'chapter_files':{path:len(groups[path]) for path in files}}
readme=f'''# Schreibbaukasten für Nicos Bachelorarbeit

DigitalStethoscope · ESP32/Zephyr · TH Augsburg · Abgabe laut Nico: **11.01.2027**.

Hier liegen geordnete Schreibbausteine aus 350 Informationseinheiten, keine fertige Thesis und keine neue Hardwarevalidierung. **{len(active)} aktive Aussagen** werden gezeigt; **{len(replaced)} ältere IDs** bleiben über „ersetzt …“ und den [Einheitenindex](einheitenindex.md) auffindbar. Die 26 Ersatz-Einheiten können dieselbe ältere ID aufteilen. Das unveränderte Verzeichnis `_stage1/` ist der Audit-Trail; sein HANDOFF beschreibt teilweise einen älteren Inventarstand.

## Jetzt mit Grundlagen anfangen

1. [Medizinische Grundlagen](02-grundlagen-medizinisch.md): Herzzyklus, S1/S2, Murmurs und Frequenzbereiche erklären.
2. [Akustik/Bruststück](03-grundlagen-technisch/01-akustik-bruststueck.md), [MEMS](03-grundlagen-technisch/02-mems-mikrofone.md) und [I²S](03-grundlagen-technisch/03-i2s-audiopfad.md): den Weg vom Herzschall zu digitalen Samples beschreiben.
3. [DSP/Filter](03-grundlagen-technisch/04-dsp-filter.md), [BPM](03-grundlagen-technisch/05-bpm-erkennung.md) und [Time-Stretch](03-grundlagen-technisch/06-time-stretch.md): Verfahren und Grenzen erläutern.
4. [Embedded/RTOS](03-grundlagen-technisch/07-embedded-rtos-esp32.md), [FHIR/TLS](03-grundlagen-technisch/08-fhir-tls.md) und [Latenz](03-grundlagen-technisch/09-latenz.md) ergänzen.

Pro Absatz eine Kernaussage wählen, Originalbeleg öffnen und die genaue Fundstelle prüfen. Zuerst allgemeine Begriffe/Mechanismen schreiben; Bauteilwahl und eigene Grenzwerte anschließend in Anforderungen/Architektur begründen. Ungeklärte Zahlen als Arbeitsnotiz stehen lassen. Die Reihenfolge innerhalb der Dateien lautet Definition → Mechanismus → Werte → Folgerung, innerhalb großer Kapitel zusätzlich nach Thema.

**Materiallücken:** Die technischen Grundlagen im Inventar sind keine vollständige Lehrbuchdarstellung. Für I²S-Taktsignale/Framing, Abtasttheorem/Quantisierung, FIR/IIR-Grundprinzipien, MEMS-Wandlungsprinzip, RTOS-Scheduling und die BPM-Schätzpipeline sind zusätzliche passende Primär- oder Lehrbuchbelege nötig. Diese Lücken verhindern das Schreiben der bereits belegten Abschnitte nicht. Historische ESP-IDF-Empfehlungen von der aktuellen Zephyr-Implementierung trennen.

## Vor Zahlenübernahme beachten

- **Widersprüche:** W1 (Q1/AP 2.2 versus gestrichene Kettenmessung), W2 (Schalterzuordnung), CirCor 5.272/5.282, Helmholtz-Modell und Knowles-LFRO. Sie stehen zuerst in [offene-punkte.md](offene-punkte.md#widersprueche).
- **Eigene Zielwerte:** 40–800 Hz / 25–150 Hz, <30 ms bzw. ≤10/≤5 ms und BPM-Akzeptanzgrenzen sind vorläufige Entwicklungsentscheidungen, keine allgemeingültigen Literaturgrenzen.
- **Quellenstand des Audits:** {stats['citation_units']} zitierbedürftige Einheiten, {stats['citation_units_with_at_least_three_sources']} davon mit mindestens drei Quellen, {stats['incomplete_source_sets']} unvollständige Quellensets. {stats['unverified_pages_exact']} von {stats['source_references']} Quellenverweisen haben exakt `page: unverified`. Nico muss diese Seiten prüfen.
- **Defekte Links:** ursprünglich 15 Einträge, betroffen 72 Einheiten. Vier verifiziert repariert, elf sichtbar defekt; weiterhin betroffen: {stats['broken_affected_units_after']} Audit-Einheiten. [Korrekturprotokoll](linkkorrekturen.md). Die Pilotstudienquelle enthält zusätzlich einen ungelösten Metadatenkonflikt.
- Build-/Host-/QC-Erfolg belegt keine integrierte physische Funktion. Historische Messungen nur mit Datum und Firmwarestand verwenden.
- **Stand integration {notes['stand']}:** W1 ist im Entwurf zugunsten der Abgabefassung ohne Kettenmessung behandelt (D09), die Bestätigung steht aus. W2 betrifft auch den im MVP optionalen Geschwindigkeitsschalter und die neue Trägerplatine. Für Latenz- und BPM-Ziele gibt es eine gemeinsame, noch nicht freigegebene Vorschlagsfassung vom 11.10. Details: [Abgleich mit integration](#abgleich-mit-integration).

## Abgleich mit integration

Die Bausteine entstanden vor neueren Projektentscheidungen auf `integration` (Stand {notes['stand']}, Commit {notes['integration_commit']}). Überholte Aussagen bleiben unverändert stehen; direkt darunter steht ein Hinweis „Überholt“ bzw. „Neuerer Stand“ mit Link auf das maßgebliche Dokument. Die Hinweise kommen aus [_build/integration-notes.json](_build/integration-notes.json) und überstehen jede Regenerierung. Nicht eindeutig entschiedene Punkte stehen unter [Offene Punkte](offene-punkte.md#integration-abgleich).

| ID | Hinweis | Was sich geändert hat |
|---|---|---|
'''
for uid,note in notes['units'].items():readme+=f'| {unit_link(uid,"README.md")} | {note["label"]} | {note["changed"]} |\n'
readme+=f'''
## Kapitelkarte

Die Zahlen zählen aktive Aussagen, nicht ersetzte IDs, Querverweise oder Quellen.

| Kapitel / Schreibdatei | Aktive Einheiten |
|---|---:|
'''
for path,title,_ in chapters:readme+=f'| [{title}]({path}) | {len(groups[path])} |\n'
readme+='''
## Marker und Nutzung

| Marker | Bedeutung beim Schreiben |
|---|---|
| LITERATURFAKT / REGEL; LITERATUR- / HERSTELLERWERT | Externe Aussage; Originalbelege und Geltungsbereich prüfen. |
| LITERATURMESSUNG / BENCHMARK | Ergebnis fremder Messung, kein Messwert dieses Prototyps. |
| EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG | Projektentscheidung oder Rechercheempfehlung; Status der tatsächlichen Übernahme prüfen. |
| EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG; EIGENE ANFORDERUNG | Eigener Sollwert/Umfang; Literatur kann begründen, macht daraus aber keine Normvorgabe. |
| EIGENER DOKUMENTIERTER BEFUND; PROJEKTDOKUMENTATION | Repository-Nachweis mit Versions-/Zeitbezug. |
| METHODENVORSCHLAG; METHODE / PRÜFVERFAHREN | Geplantes oder beschriebenes Vorgehen; Durchführung gesondert nachweisen. |
| ANNAHME / OFFEN / WIDERSPRUCH / RISIKO | Noch prüfen oder entscheiden; nicht stillschweigend als erwiesen übernehmen. |
| QUELLENSET UNVOLLSTÄNDIG | Stage-1-Flag; Belegqualität prüfen und Lücke bearbeiten. |
| Seite prüfen | Keine verifizierte Seitenzahl; vorhandener Hinweis ist nur eine Suchhilfe. |
| 🔒 / LINK DEFEKT | Volltextzugang eingeschränkt/ungeklärt oder Link nicht zuverlässig erreichbar. |
| ersetzt U… | Aktueller Schreibbaustein ersetzt diese Audit-ID; Original im Audit nachlesbar. |

`confirmed` wird nicht eigens angezeigt: Es bedeutet im Inventar dokumentiert, nicht unabhängig wahrheitsgeprüft. Auch vorhandene Abschnitts-/Tabellenverweise sind aus Stage 1 übernommen. Alle Aussagen behalten exakt ihre Quellsprache; einzelne englische Firmwareeinheiten sind deshalb weiterhin Englisch.

[Quellenverzeichnis](quellen.md) führt alle 103 Schlüssel mit zitierenden IDs. [quellen.bib](quellen.bib) enthält konservative Minimal-Einträge und kennzeichnet fehlende Metadaten; es ist noch kein abgabefertiges Literaturverzeichnis. [Einheitenindex](einheitenindex.md) führt jede Audit-ID zur Schreibstelle. [Offene Punkte](offene-punkte.md) sind die Arbeitsliste für Entscheidungen, Seiten und Quellenlücken.

## Regenerieren und prüfen

```bash
python thesis-material/_build/build.py
```

Der Generator benötigt nur die Python-Standardbibliothek und keinen Netzwerkzugang. Redaktionelle Änderungen im Generator bzw. in `_build/source-overrides.json` pflegen; erzeugte Dateien werden überschrieben. `_stage1/` wird ausschließlich gelesen. Die Vollständigkeitsprüfung kontrolliert alle 350 IDs in den Kapiteldateien, jede aktive Aussage genau einmal, alle Quellenreferenzen und lokale Linkziele. Ergebnis: [vollstaendigkeit.md](vollstaendigkeit.md); maschinenlesbar: [_build/check.json](_build/check.json).

'''+WATERMARK+'\n'
outputs['README.md']=readme

# Vollständigkeit muss in den Kapiteldateien selbst erfüllt sein; der Index allein genügt nicht.
chapter_text='\n'.join(outputs[p] for p in files)
visible=set(re.findall(r'\b[UABC]\d{3}\b',chapter_text))
assert set(by_id)<=visible, f'Fehlende IDs: {set(by_id)-visible}'
assert not visible-set(by_id), f'Unbekannte IDs: {visible-set(by_id)}'
for u in active:assert chapter_text.count(f'<a id="{u["id"].lower()}"></a>')==1
for old in replaced:assert not re.search(f'<a id="{old.lower()}"></a>',chapter_text)
assert all(stage1_before[str(p.relative_to(ROOT))]==hashlib.sha256(p.read_bytes()).hexdigest() for p in AUDIT.rglob('*') if p.is_file())
for path,content in outputs.items():
    dest=ROOT/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(content,encoding='utf-8',newline=LF)
# Lokale Markdownziele prüfen (Line-Fragmente sind Herkunftshinweise, keine neue Zeilenprüfung).
missing=[]
for path,content in outputs.items():
    if not path.endswith('.md'):continue
    for href in re.findall(r'\]\(([^)]+)\)',content):
        if href.startswith(('http://','https://')):continue
        from urllib.parse import unquote
        target=href.split('#')[0]
        if target and not ((ROOT/path).parent/unquote(target)).exists() and ((ROOT/path).parent/unquote(target)).resolve() not in {ROOT/'vollstaendigkeit.md', ROOT/'_build/check.json'}:missing.append((path,href))
assert not missing, f'Defekte lokale Ziele: {missing}'
stats.update({'coverage':'350/350', 'missing_ids':[], 'active_statements_once':True,
 'stage1_unchanged_during_build':True,'local_link_targets':'ok',
 'integration_notes':len(notes['units']),'integration_refs_checked':sorted(checked_refs),
 'relocated_origins':sorted(notes['relocated_origins']),'missing_origins':sorted(missing_origins)})
(ROOT/'_build/check.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline=LF)
report=f'''# Vollständigkeitsprüfung

**PASS: 350/350 Audit-IDs in den Kapiteldateien vorhanden.**

- {len(active)} aktive Aussagen jeweils genau einmal mit eigenem Anker.
- {len(replaced)} ersetzte IDs ausdrücklich als „ersetzt …“ erhalten; 26 Ersatz-Einheiten.
- 103 Quellenschlüssel; alle Quellenverweise auf bekannte Einträge.
- Alle lokalen Markdown-Linkziele vorhanden.
- `_stage1/` während des Generatorlaufs unverändert (SHA-256-Vergleich).
- Fehlende IDs: keine. Unbekannte IDs: keine.
- {len(notes['units'])} Abgleichshinweise gegen integration; alle {len(checked_refs)} verlinkten integration-Dokumente/Anker vorhanden.
- Verschobene Herkunftsdateien mit historischem Git-Link: {len(notes['relocated_origins'])}; nicht auflösbare Herkunftsdateien: {len(missing_origins)}.

Audit-Zählung: {stats['citation_units']} zitierbedürftige Einheiten; {stats['citation_units_with_at_least_three_sources']} mit mindestens drei Quellen; {stats['incomplete_source_sets']} unvollständige Quellensets; {stats['unverified_pages_exact']}/{stats['source_references']} explizit ungeprüfte Seiten. Defekte Quellen: {len(broken_before)} → {len(broken_after)}; betroffene Audit-Einheiten: {stats['broken_affected_units_before']} → {stats['broken_affected_units_after']}.

Die Prüfung belegt Vollständigkeit und Verlinkung des Baukastens, keine wissenschaftliche Richtigkeit oder fertige Grundlagenabdeckung. [Maschinenlesbarer Bericht](_build/check.json).

'''+WATERMARK+'\n'
(ROOT/'vollstaendigkeit.md').write_text(report,encoding='utf-8',newline=LF)
print(json.dumps(stats,ensure_ascii=False,indent=2))
