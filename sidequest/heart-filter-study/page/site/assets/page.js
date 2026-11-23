(function () {
  "use strict";

  var root = document.documentElement;
  var scriptErrors = [];
  window.addEventListener("error", function (event) {
    scriptErrors.push(String(event.message || event.type));
    root.setAttribute("data-script-errors", scriptErrors.join(" | "));
  });
  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // In-page navigation by scrolling only: the host sandbox throws on every History API call.
  document.addEventListener("click", function (event) {
    var link = event.target.closest ? event.target.closest('a[href^="#"]') : null;
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey) return;
    var identifier = decodeURIComponent(link.getAttribute("href").slice(1));
    var target = identifier ? document.getElementById(identifier) : null;
    if (!target) return;
    event.preventDefault();
    var mobileContents = link.closest("details.toc-mobile");
    if (mobileContents) mobileContents.open = false;
    target.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
    if (!target.hasAttribute("tabindex") && !/^(A|BUTTON|INPUT|SELECT|TEXTAREA)$/.test(target.tagName)) target.setAttribute("tabindex", "-1");
    try { target.focus({ preventScroll: true }); } catch (error) { target.focus(); }
    if (target.matches("li[id^='source-']")) {
      target.classList.add("is-flashed");
      setTimeout(function () { target.classList.remove("is-flashed"); }, 1600);
    }
  });

  function markCurrentSection() {
    var links = Array.prototype.slice.call(document.querySelectorAll(".toc-sidebar a"));
    if (!links.length || !("IntersectionObserver" in window)) return;
    var headings = links.map(function (link) { return document.getElementById(link.getAttribute("href").slice(1)); });
    var visible = {};
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) { visible[entry.target.id] = entry.isIntersecting; });
      var current = null;
      for (var index = 0; index < headings.length; index++) {
        var heading = headings[index];
        if (!heading) continue;
        if (heading.getBoundingClientRect().top < window.innerHeight * 0.35) current = heading.id;
      }
      links.forEach(function (link) { link.classList.toggle("is-current", link.getAttribute("href") === "#" + current); });
    }, { rootMargin: "0px 0px -60% 0px" });
    headings.forEach(function (heading) { if (heading) observer.observe(heading); });
  }

  function setUpFigureOverlay() {
    var overlay = document.querySelector(".figure-overlay");
    if (!overlay) return;
    var image = overlay.querySelector("img");
    var caption = overlay.querySelector(".figure-overlay-caption");
    var closeButton = overlay.querySelector(".figure-overlay-close");
    var opener = null;
    function close() {
      if (overlay.hidden) return;
      overlay.hidden = true;
      image.removeAttribute("src");
      document.body.style.overflow = "";
      if (opener) opener.focus();
    }
    document.querySelectorAll(".figure-open").forEach(function (button) {
      button.addEventListener("click", function () {
        opener = button;
        var figureImage = button.querySelector("img");
        image.src = button.getAttribute("data-full");
        image.alt = figureImage ? figureImage.alt : "";
        var figureCaption = button.parentNode.querySelector("figcaption");
        caption.textContent = figureCaption ? figureCaption.textContent : "";
        overlay.hidden = false;
        document.body.style.overflow = "hidden";
        closeButton.focus();
      });
    });
    overlay.addEventListener("click", close);
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") close();
      if (event.key === "Tab" && !overlay.hidden) { event.preventDefault(); closeButton.focus(); }
    });
  }

  /* ---------- Audio comparison player ---------- */

  var players = [];
  var sharedAudioContext = null;
  var webAudioUnavailableReason = null;
  var fetchCapability = null;
  var fetchWorks = null;
  var CROSS_FADE_SECONDS = 0.015;
  var TRANSPORT_ICONS = {
    play: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2.5v11l9-5.5z"/></svg>',
    pause: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 2.5h3v11h-3zM9.5 2.5h3v11h-3z"/></svg>'
  };

  function probeFetch(url) {
    if (fetchCapability) return fetchCapability;
    if (!window.fetch || location.protocol === "file:") {
      fetchWorks = false;
      fetchCapability = Promise.resolve(false);
      return fetchCapability;
    }
    fetchCapability = fetch(url, { method: "HEAD", cache: "force-cache" })
      .then(function (response) { return response.ok; })
      .catch(function () { return false; })
      .then(function (works) { fetchWorks = works; return works; });
    return fetchCapability;
  }

  function getAudioContext() {
    if (sharedAudioContext) return sharedAudioContext;
    var Constructor = window.AudioContext || window.webkitAudioContext;
    if (!Constructor) { webAudioUnavailableReason = "Web Audio is not available"; return null; }
    try { sharedAudioContext = new Constructor(); } catch (error) { webAudioUnavailableReason = String(error); return null; }
    return sharedAudioContext;
  }

  // iOS only starts a context from inside a user gesture; a silent one-sample buffer unlocks it.
  function unlockAudioContext(context) {
    try {
      var silent = context.createBuffer(1, 1, 22050);
      var source = context.createBufferSource();
      source.buffer = silent;
      source.connect(context.destination);
      source.start(0);
    } catch (error) { /* unlocking is best effort */ }
    if (context.state !== "running" && context.resume) context.resume().catch(function () {});
  }

  function decodeBuffer(context, arrayBuffer) {
    return new Promise(function (resolve, reject) {
      var settled = false;
      var promise = context.decodeAudioData(arrayBuffer, function (buffer) { settled = true; resolve(buffer); },
        function (error) { settled = true; reject(error || new Error("decodeAudioData failed")); });
      if (promise && promise.then) promise.then(function (buffer) { if (!settled) resolve(buffer); }, function (error) { if (!settled) reject(error); });
    });
  }

  function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) seconds = 0;
    var minutes = Math.floor(seconds / 60);
    var rest = seconds - minutes * 60;
    return minutes + ":" + (rest < 10 ? "0" : "") + rest.toFixed(1);
  }

  function formatNumber(value, decimals, unit) {
    if (value === null || value === undefined || !isFinite(value)) return "–";
    var text = Number(value).toFixed(decimals).replace("-", "−");
    if (Number(value) > 0 && unit === "dB") text = "+" + text;
    return text + (unit ? " " + unit : "");
  }

  function formatBoost(value) {
    if (value === null || value === undefined || !isFinite(value)) return "boost –";
    if (Number(value) === 0) return "boost 0 dB";
    // Rounding down keeps the shown boost at or below the largest safe one, so a shown value never overloads.
    var roundedDown = Math.floor(Number(value) * 100 + 1e-9) / 100;
    return "boost " + (roundedDown > 0 ? "+" : "") + roundedDown.toFixed(2).replace("-", "−") + " dB";
  }

  function formatPeak(value) {
    if (value === null || value === undefined || !isFinite(value)) return "peak –";
    if (Number(value) >= 0) return "peak at full scale";
    var distance = -Number(value);
    return distance < 0.05 ? "peak less than 0.1 dB below full scale" : "peak " + distance.toFixed(1) + " dB below full scale";
  }

  function decodePeaks(base64Text) {
    if (!base64Text) return null;
    try {
      var binary = atob(base64Text);
      var peaks = new Float32Array(binary.length);
      for (var index = 0; index < binary.length; index++) {
        var byte = binary.charCodeAt(index);
        peaks[index] = (byte > 127 ? byte - 256 : byte) / 127;
      }
      return peaks;
    } catch (error) { return null; }
  }

  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function shuffled(values) {
    var copy = values.slice();
    for (var index = copy.length - 1; index > 0; index--) {
      var other = Math.floor(Math.random() * (index + 1));
      var swap = copy[index]; copy[index] = copy[other]; copy[other] = swap;
    }
    return copy;
  }

  function ComparisonPlayer(section, configuration) {
    this.section = section;
    this.configuration = configuration;
    this.variantIndex = 0;
    this.selectedIdentifier = null;
    this.order = [];
    this.blind = false;
    this.revealed = false;
    this.looping = true;
    this.volume = 0.8;
    this.playing = false;
    this.loading = false;
    this.pausedPosition = 0;
    this.engine = null;
    this.buffers = {};
    this.voice = null;
    this.masterGain = null;
    this.audioElements = {};
    this.currentElement = null;
    this.audibleElement = null;
    this.switchToken = 0;
    this.animationFrame = null;
    this.build();
  }

  ComparisonPlayer.prototype.currentVariant = function () { return this.configuration.variants[this.variantIndex]; };
  ComparisonPlayer.prototype.samples = function () { return this.currentVariant().samples; };
  ComparisonPlayer.prototype.selectedSample = function () {
    var samples = this.samples();
    for (var index = 0; index < samples.length; index++) if (samples[index].identifier === this.selectedIdentifier) return samples[index];
    return samples[0];
  };
  ComparisonPlayer.prototype.duration = function () {
    var sample = this.selectedSample();
    if (this.engine === "webaudio" && sample && this.buffers[sample.url]) return this.buffers[sample.url].duration;
    if (this.engine === "element" && this.currentElement && isFinite(this.currentElement.duration)) return this.currentElement.duration;
    return sample && sample.duration ? sample.duration : 0;
  };

  ComparisonPlayer.prototype.build = function () {
    var player = this;
    var mount = this.section.querySelector(".player-mount");
    mount.textContent = "";

    if (this.configuration.variants.length > 1) {
      this.variantControl = element("div", "segmented");
      this.variantControl.setAttribute("role", "group");
      this.variantControl.setAttribute("aria-label", "Playback variant");
      this.configuration.variants.forEach(function (variant, index) {
        var button = element("button", "", variant.label);
        button.type = "button";
        button.addEventListener("click", function () { player.selectVariant(index); });
        player.variantControl.appendChild(button);
      });
      mount.appendChild(this.variantControl);
    }
    this.explanation = element("p", "variant-explanation");
    mount.appendChild(this.explanation);

    var toolbar = element("div", "candidate-toolbar");
    toolbar.appendChild(element("span", "candidate-hint", "Tap a filter to switch while it plays. Keys 1–9 switch, space plays or pauses."));
    var toolbarButtons = element("div", "toolbar-buttons");
    this.blindButton = element("button", "", "Hide names");
    this.blindButton.type = "button";
    this.blindButton.setAttribute("aria-pressed", "false");
    this.blindButton.addEventListener("click", function () { player.setBlind(!player.blind); });
    this.revealButton = element("button", "", "Reveal");
    this.revealButton.type = "button";
    this.revealButton.hidden = true;
    this.revealButton.addEventListener("click", function () { player.revealed = !player.revealed; player.renderCandidates(); });
    toolbarButtons.appendChild(this.blindButton);
    toolbarButtons.appendChild(this.revealButton);
    toolbar.appendChild(toolbarButtons);
    mount.appendChild(toolbar);

    this.candidateList = element("ul", "candidate-list");
    this.candidateList.setAttribute("role", "list");
    mount.appendChild(this.candidateList);
    this.metadataLegend = element("p", "candidate-legend", "Boost: fixed amplification applied in this variant. Peak: largest value of the excerpt. Loudness: broadcast loudness measure (ITU-R BS.1770-4), in its unit LUFS; higher is louder.");
    mount.appendChild(this.metadataLegend);

    this.waveform = element("div", "waveform");
    this.waveform.setAttribute("aria-hidden", "true");
    this.canvas = document.createElement("canvas");
    this.playhead = element("div", "waveform-playhead");
    this.waveform.appendChild(this.canvas);
    this.waveform.appendChild(this.playhead);
    this.waveform.appendChild(element("span", "waveform-legend", "full scale"));
    this.waveform.addEventListener("pointerdown", function (event) {
      var bounds = player.waveform.getBoundingClientRect();
      player.seek(Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width)) * player.duration());
    });
    mount.appendChild(this.waveform);

    var transport = element("div", "transport");
    this.playButton = element("button", "play-button");
    this.playButton.type = "button";
    this.playButton.addEventListener("click", function () { player.togglePlay(); });
    transport.appendChild(this.playButton);
    var seekGroup = element("div", "seek-group");
    this.elapsedDisplay = element("span", "time-display", "0:00.0");
    this.seekBar = document.createElement("input");
    this.seekBar.type = "range"; this.seekBar.min = "0"; this.seekBar.max = "1000"; this.seekBar.step = "1"; this.seekBar.value = "0";
    this.seekBar.setAttribute("aria-label", "Playback position");
    this.seekBar.addEventListener("input", function () { player.seek(Number(player.seekBar.value) / 1000 * player.duration()); });
    this.durationDisplay = element("span", "time-display", "0:00.0");
    seekGroup.appendChild(this.elapsedDisplay);
    seekGroup.appendChild(this.seekBar);
    seekGroup.appendChild(this.durationDisplay);
    transport.appendChild(seekGroup);
    this.loopButton = element("button", "loop-button", "Loop");
    this.loopButton.type = "button";
    this.loopButton.addEventListener("click", function () { player.setLooping(!player.looping); });
    transport.appendChild(this.loopButton);
    var volumeGroup = element("label", "volume-group");
    volumeGroup.appendChild(element("span", "", "Volume"));
    this.volumeSlider = document.createElement("input");
    this.volumeSlider.type = "range"; this.volumeSlider.min = "0"; this.volumeSlider.max = "100"; this.volumeSlider.value = String(this.volume * 100);
    this.volumeSlider.addEventListener("input", function () { player.setVolume(Number(player.volumeSlider.value) / 100); });
    volumeGroup.appendChild(this.volumeSlider);
    transport.appendChild(volumeGroup);
    mount.appendChild(transport);

    this.status = element("p", "player-status");
    this.status.setAttribute("role", "status");
    this.status.setAttribute("aria-live", "polite");
    mount.appendChild(this.status);

    this.section.addEventListener("keydown", function (event) { player.handleKey(event); });
    if (window.ResizeObserver) new ResizeObserver(function () { player.drawWaveform(); }).observe(this.waveform);
    else window.addEventListener("resize", function () { player.drawWaveform(); });

    this.resetOrder();
    this.renderVariant();
    this.updateTransport();
    var firstSample = this.samples()[0];
    if (firstSample) probeFetch(firstSample.url);
    this.setStatus("Ready. Press play; switching filters keeps the position.");
  };

  ComparisonPlayer.prototype.setStatus = function (text, kind) {
    this.status.textContent = text;
    this.status.className = "player-status" + (kind === "error" ? " is-error" : kind === "busy" ? " is-busy" : "");
  };

  ComparisonPlayer.prototype.resetOrder = function () {
    var identifiers = this.samples().map(function (sample) { return sample.identifier; });
    this.order = this.blind ? shuffled(identifiers) : identifiers;
    var selected = this.selectedIdentifier;
    if (!selected || identifiers.indexOf(selected) < 0) {
      var firstPlayable = this.samples().filter(function (sample) { return !sample.missing; })[0];
      this.selectedIdentifier = firstPlayable ? firstPlayable.identifier : identifiers[0];
    }
  };

  ComparisonPlayer.prototype.renderVariant = function () {
    var player = this;
    if (this.variantControl) {
      Array.prototype.forEach.call(this.variantControl.children, function (button, index) {
        button.setAttribute("aria-pressed", index === player.variantIndex ? "true" : "false");
      });
    }
    this.explanation.textContent = this.currentVariant().explanation || "";
    this.explanation.hidden = !this.currentVariant().explanation;
    this.renderCandidates();
  };

  ComparisonPlayer.prototype.renderCandidates = function () {
    var player = this;
    var samplesByIdentifier = {};
    this.samples().forEach(function (sample) { samplesByIdentifier[sample.identifier] = sample; });
    this.candidateList.textContent = "";
    this.blindButton.setAttribute("aria-pressed", this.blind ? "true" : "false");
    this.revealButton.hidden = !this.blind;
    this.revealButton.textContent = this.revealed ? "Hide again" : "Reveal";
    this.revealButton.setAttribute("aria-pressed", this.revealed ? "true" : "false");
    this.metadataLegend.hidden = this.blind && !this.revealed;
    this.order.forEach(function (identifier, position) {
      var sample = samplesByIdentifier[identifier];
      var letter = String.fromCharCode(65 + (position % 26));
      var item = element("li");
      var button = element("button", "candidate");
      button.type = "button";
      button.setAttribute("aria-pressed", identifier === player.selectedIdentifier ? "true" : "false");
      button.appendChild(element("span", "candidate-key", position < 9 ? String(position + 1) : "·"));
      var labelText = player.blind ? (player.revealed ? letter + " · " + sample.label : "Sample " + letter) : sample.label;
      if (sample.missing) labelText += " (file missing)";
      button.appendChild(element("span", "candidate-label", labelText));
      if (!player.blind || player.revealed) {
        var meta = element("span", "candidate-meta");
        meta.appendChild(element("span", "", formatBoost(sample.applied_gain_db)));
        meta.appendChild(element("span", "", formatPeak(sample.output_peak_dbfs)));
        if (sample.k_weighted_level_lufs !== null && sample.k_weighted_level_lufs !== undefined) {
          meta.appendChild(element("span", "", "loudness " + formatNumber(sample.k_weighted_level_lufs, 1, "LUFS")));
        }
        var clipped = sample.clipped_samples;
        var clippedText = clipped === null || clipped === undefined ? "values cut off –" : clipped > 0 ? "values cut off: " + clipped : "no values cut off";
        meta.appendChild(element("span", clipped > 0 ? "is-clipped" : "", clippedText));
        button.appendChild(meta);
      }
      button.setAttribute("aria-label", labelText + (position < 9 ? ", key " + (position + 1) : ""));
      if (sample.missing) button.disabled = true;
      button.addEventListener("click", function () { player.selectSample(identifier); });
      item.appendChild(button);
      player.candidateList.appendChild(item);
    });
    this.drawWaveform();
  };

  ComparisonPlayer.prototype.setBlind = function (blind) {
    this.blind = blind;
    this.revealed = false;
    this.resetOrder();
    this.renderCandidates();
  };

  ComparisonPlayer.prototype.handleKey = function (event) {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    var targetTag = event.target.tagName;
    if (event.key === " " || event.key === "Spacebar") {
      if (targetTag === "INPUT" && event.target.type !== "range") return;
      event.preventDefault();
      this.togglePlay();
    } else if (/^[1-9]$/.test(event.key)) {
      var identifier = this.order[Number(event.key) - 1];
      if (identifier) { event.preventDefault(); this.selectSample(identifier); }
    }
  };

  ComparisonPlayer.prototype.position = function () {
    if (!this.playing) return this.pausedPosition;
    if (this.engine === "webaudio" && this.voice) {
      var elapsed = sharedAudioContext.currentTime - this.voice.startContextTime + this.voice.startOffset;
      var duration = this.voice.duration;
      return this.voice.source.loop ? elapsed % duration : Math.min(elapsed, duration);
    }
    var heardElement = this.audibleElement || this.currentElement;
    if (this.engine === "element" && heardElement) return heardElement.currentTime;
    return this.pausedPosition;
  };

  ComparisonPlayer.prototype.togglePlay = function () {
    if (this.playing || this.loading) this.pause();
    else this.play();
  };

  ComparisonPlayer.prototype.play = function () {
    var player = this;
    players.forEach(function (other) { if (other !== player && (other.playing || other.loading)) other.pause(); });
    var sample = this.selectedSample();
    if (!sample || sample.missing) { this.setStatus("This sample is missing and cannot be played.", "error"); return; }
    if (this.engine === null) {
      var context = getAudioContext();
      if (context) unlockAudioContext(context);
      this.engine = context && context.decodeAudioData && fetchWorks !== false ? "webaudio-pending" : "element";
    }
    if (this.engine === "element") { this.playElement(this.position()); return; }
    if (sharedAudioContext.state !== "running" && sharedAudioContext.resume) sharedAudioContext.resume().catch(function () {});
    this.loading = true;
    this.updateTransport();
    this.setStatus("Loading samples…", "busy");
    var startPosition = this.pausedPosition;
    var variantIndexAtStart = this.variantIndex;
    var firstUrl = sample.url;
    probeFetch(firstUrl).then(function (fetchAllowed) {
      if (!fetchAllowed) throw new Error("fetch of audio files is not allowed here");
      return player.loadBuffers();
    }).then(function () {
      if (!player.loading || player.variantIndex !== variantIndexAtStart) return;
      player.loading = false;
      player.engine = "webaudio";
      player.startVoice(startPosition, false);
      player.setPlaying(true);
      player.setStatus("Playing with Web Audio: switching is seamless.");
    }).catch(function (error) {
      if (!player.loading) return;
      player.loading = false;
      player.engine = "element";
      player.setStatus("Using the browser's audio elements (" + (error && error.message ? error.message : error) + ").");
      player.playElement(startPosition);
    });
  };

  ComparisonPlayer.prototype.loadBuffers = function () {
    var player = this;
    var context = sharedAudioContext;
    var pending = this.samples().filter(function (sample) { return !sample.missing && !player.buffers[sample.url]; });
    return Promise.all(pending.map(function (sample) {
      return fetch(sample.url).then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status + " for " + sample.url);
        return response.arrayBuffer();
      }).then(function (bytes) { return decodeBuffer(context, bytes); })
        .then(function (buffer) { player.buffers[sample.url] = buffer; });
    }));
  };

  ComparisonPlayer.prototype.ensureMasterGain = function () {
    if (this.masterGain) return;
    this.masterGain = sharedAudioContext.createGain();
    this.masterGain.gain.value = this.volume;
    this.masterGain.connect(sharedAudioContext.destination);
  };

  ComparisonPlayer.prototype.startVoice = function (offset, crossFade) {
    var player = this;
    var context = sharedAudioContext;
    var buffer = this.buffers[this.selectedSample().url];
    if (!buffer) return;
    this.ensureMasterGain();
    var source = context.createBufferSource();
    source.buffer = buffer;
    source.loop = this.looping;
    var gain = context.createGain();
    source.connect(gain);
    gain.connect(this.masterGain);
    var now = context.currentTime;
    var safeOffset = Math.max(0, offset);
    safeOffset = this.looping ? safeOffset % buffer.duration : Math.min(safeOffset, buffer.duration);
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(1, now + CROSS_FADE_SECONDS);
    var voice = { source: source, gain: gain, startContextTime: now, startOffset: safeOffset, duration: buffer.duration };
    source.onended = function () {
      if (player.voice !== voice) return;
      player.voice = null;
      player.pausedPosition = 0;
      player.setPlaying(false);
    };
    source.start(now, safeOffset);
    var previous = this.voice;
    this.voice = voice;
    if (previous) this.retireVoice(previous, crossFade ? CROSS_FADE_SECONDS : 0.005);
  };

  ComparisonPlayer.prototype.retireVoice = function (voice, fadeSeconds) {
    var now = sharedAudioContext.currentTime;
    try {
      voice.gain.gain.cancelScheduledValues(now);
      voice.gain.gain.setValueAtTime(voice.gain.gain.value, now);
      voice.gain.gain.linearRampToValueAtTime(0, now + fadeSeconds);
      voice.source.onended = null;
      voice.source.stop(now + fadeSeconds + 0.01);
    } catch (error) { /* already stopped */ }
  };

  ComparisonPlayer.prototype.audioElementFor = function (sample) {
    var player = this;
    var audio = this.audioElements[sample.url];
    if (audio) return audio;
    audio = document.createElement("audio");
    audio.preload = "auto";
    audio.src = sample.url;
    audio.loop = this.looping;
    audio.volume = this.volume;
    audio.addEventListener("ended", function () {
      if (player.currentElement !== audio) return;
      player.pausedPosition = 0;
      player.setPlaying(false);
    });
    audio.addEventListener("error", function () {
      if (player.currentElement !== audio) return;
      player.setPlaying(false);
      player.setStatus("Could not load “" + sample.label + "” (" + sample.url + "). The file may be missing or blocked by the host.", "error");
    });
    this.audioElements[sample.url] = audio;
    return audio;
  };

  // The new element starts muted inside the tap handler (iOS only allows play() there) while the old one
  // stays audible; the swap happens once the seek has landed, because servers without HTTP Range support
  // cannot seek into data that is not buffered yet.
  ComparisonPlayer.prototype.playElement = function (position) {
    var player = this;
    var sample = this.selectedSample();
    var audio = this.audioElementFor(sample);
    this.samples().forEach(function (other) { if (!other.missing) player.audioElementFor(other); });
    var audible = this.audibleElement;
    var previous = audible && audible !== audio && !audible.paused ? audible : null;
    for (var url in this.audioElements) {
      var other = this.audioElements[url];
      if (other !== audio && other !== previous) { other.pause(); other.muted = false; }
    }
    this.currentElement = audio;
    this.switchToken = (this.switchToken || 0) + 1;
    var token = this.switchToken;
    audio.loop = this.looping;
    audio.volume = this.volume;
    var retryEvents = ["loadedmetadata", "canplay", "canplaythrough", "progress"];
    var timer = null;
    function targetPosition() {
      var target = previous ? previous.currentTime : position;
      return isFinite(audio.duration) && audio.duration > 0 ? target % audio.duration : target;
    }
    function trySeek() {
      if (audio.readyState < 1) return false;
      var target = targetPosition();
      try { audio.currentTime = target; } catch (error) { return false; }
      return Math.abs(audio.currentTime - target) < 0.3;
    }
    function finish() {
      retryEvents.forEach(function (name) { audio.removeEventListener(name, retry); });
      clearTimeout(timer);
      if (token !== player.switchToken) return;
      audio.muted = false;
      if (previous) previous.pause();
      player.audibleElement = audio;
    }
    function retry() { if (trySeek()) finish(); }
    if (trySeek()) {
      finish();
    } else {
      audio.muted = !!previous;
      if (!previous) player.audibleElement = audio;
      retryEvents.forEach(function (name) { audio.addEventListener(name, retry); });
      timer = setTimeout(finish, 2500);
    }
    var result = audio.play();
    if (!/Using the browser/.test(this.status.textContent)) {
      this.setStatus("Playing with the browser's audio elements: switching works, with a possible small click.");
    }
    this.setPlaying(true);
    if (result && result.catch) {
      result.catch(function (error) {
        if (player.currentElement !== audio) return;
        player.setPlaying(false);
        player.pausedPosition = position;
        player.setStatus(error && error.name === "NotAllowedError" ? "The browser blocked playback. Tap play again." :
          "Playback failed: " + (error && error.message ? error.message : error), "error");
      });
    }
  };

  ComparisonPlayer.prototype.pause = function () {
    var position = this.position();
    if (this.loading) this.loading = false;
    if (this.engine === "webaudio" && this.voice) { this.retireVoice(this.voice, 0.008); this.voice = null; }
    if (this.engine === "element") {
      this.switchToken = (this.switchToken || 0) + 1;
      for (var url in this.audioElements) { this.audioElements[url].pause(); this.audioElements[url].muted = false; }
      if (this.currentElement) this.audibleElement = this.currentElement;
    }
    this.pausedPosition = position;
    this.setPlaying(false);
    if (/Loading/.test(this.status.textContent)) this.setStatus("Paused.");
  };

  ComparisonPlayer.prototype.selectSample = function (identifier) {
    var samples = this.samples();
    var sample = samples.filter(function (candidate) { return candidate.identifier === identifier; })[0];
    if (!sample || sample.missing || identifier === this.selectedIdentifier) {
      if (sample && identifier === this.selectedIdentifier && !this.playing && !this.loading) this.play();
      return;
    }
    var position = this.position();
    this.selectedIdentifier = identifier;
    if (this.playing && this.engine === "webaudio") this.startVoice(position, true);
    else if (this.playing && this.engine === "element") this.playElement(position);
    else this.pausedPosition = position;
    var player = this;
    Array.prototype.forEach.call(this.candidateList.querySelectorAll(".candidate"), function (button, index) {
      button.setAttribute("aria-pressed", player.order[index] === identifier ? "true" : "false");
    });
    this.drawWaveform();
    this.updateTransport();
  };

  ComparisonPlayer.prototype.selectVariant = function (index) {
    if (index === this.variantIndex) return;
    var wasActive = this.playing || this.loading;
    var position = this.position();
    if (wasActive) this.pause();
    this.variantIndex = index;
    this.pausedPosition = position;
    this.resetOrder();
    this.renderVariant();
    this.updateTransport();
    if (wasActive) this.play();
  };

  ComparisonPlayer.prototype.seek = function (seconds) {
    var duration = this.duration();
    if (!(duration > 0)) return;
    seconds = Math.max(0, Math.min(seconds, duration - 0.001));
    if (this.playing && this.engine === "webaudio") this.startVoice(seconds, true);
    else if (this.playing && this.engine === "element" && (this.audibleElement || this.currentElement)) (this.audibleElement || this.currentElement).currentTime = seconds;
    else this.pausedPosition = seconds;
    this.updateTransport();
  };

  ComparisonPlayer.prototype.setLooping = function (looping) {
    var position = this.position();
    this.looping = looping;
    if (this.voice) {
      this.voice.source.loop = looping;
      this.voice.startOffset = position;
      this.voice.startContextTime = sharedAudioContext.currentTime;
    }
    for (var url in this.audioElements) this.audioElements[url].loop = looping;
    this.updateTransport();
  };

  ComparisonPlayer.prototype.setVolume = function (volume) {
    this.volume = volume;
    if (this.masterGain) this.masterGain.gain.setTargetAtTime(volume, sharedAudioContext.currentTime, 0.01);
    for (var url in this.audioElements) this.audioElements[url].volume = volume;
  };

  ComparisonPlayer.prototype.setPlaying = function (playing) {
    var player = this;
    this.playing = playing;
    this.updateTransport();
    if (playing && this.animationFrame === null) {
      var step = function () {
        player.updateTransport();
        player.animationFrame = player.playing ? requestAnimationFrame(step) : null;
      };
      this.animationFrame = requestAnimationFrame(step);
    }
  };

  ComparisonPlayer.prototype.updateTransport = function () {
    var active = this.playing || this.loading;
    this.playButton.innerHTML = (active ? TRANSPORT_ICONS.pause : TRANSPORT_ICONS.play) + "<span>" + (this.loading ? "Loading" : active ? "Pause" : "Play") + "</span>";
    this.playButton.setAttribute("aria-label", active ? "Pause" : "Play");
    this.section.setAttribute("aria-busy", this.loading ? "true" : "false");
    this.loopButton.setAttribute("aria-pressed", this.looping ? "true" : "false");
    var duration = this.duration();
    var position = this.position();
    this.elapsedDisplay.textContent = formatTime(position);
    this.durationDisplay.textContent = formatTime(duration);
    var fraction = duration > 0 ? Math.min(1, position / duration) : 0;
    if (document.activeElement !== this.seekBar || this.playing) this.seekBar.value = String(Math.round(fraction * 1000));
    this.playhead.style.left = (fraction * 100).toFixed(3) + "%";
  };

  ComparisonPlayer.prototype.drawWaveform = function () {
    var sample = this.selectedSample();
    var peaks = sample ? (sample.decodedPeaks || (sample.decodedPeaks = decodePeaks(sample.peaks))) : null;
    var canvas = this.canvas;
    var width = Math.max(1, Math.round(this.waveform.clientWidth * (window.devicePixelRatio || 1)));
    var height = Math.max(1, Math.round(this.waveform.clientHeight * (window.devicePixelRatio || 1)));
    if (canvas.width !== width) canvas.width = width;
    if (canvas.height !== height) canvas.height = height;
    var context = canvas.getContext("2d");
    if (!context) return;
    var style = getComputedStyle(document.documentElement);
    context.clearRect(0, 0, width, height);
    var middle = height / 2;
    var fullScale = height * 0.42;
    context.fillStyle = style.getPropertyValue("--divider").trim() || "#192021";
    context.fillRect(0, Math.round(middle), width, 1);
    context.fillStyle = style.getPropertyValue("--bad").trim() || "#f08a7c";
    context.globalAlpha = 0.7;
    context.fillRect(0, Math.round(middle - fullScale), width, 1);
    context.fillRect(0, Math.round(middle + fullScale), width, 1);
    context.globalAlpha = 1;
    if (!peaks || peaks.length < 2) return;
    var bucketCount = peaks.length / 2;
    var accent = style.getPropertyValue("--accent").trim() || "#52c7b4";
    var bad = style.getPropertyValue("--bad").trim() || "#f08a7c";
    for (var x = 0; x < width; x++) {
      var bucket = Math.min(bucketCount - 1, Math.floor(x / width * bucketCount));
      var minimum = peaks[bucket * 2];
      var maximum = peaks[bucket * 2 + 1];
      context.fillStyle = (maximum >= 0.995 || minimum <= -0.995) ? bad : accent;
      var top = middle - maximum * fullScale;
      var bottom = middle - minimum * fullScale;
      context.fillRect(x, top, 1, Math.max(1, bottom - top));
    }
  };

  function setUpPlayers() {
    document.querySelectorAll("[data-player]").forEach(function (section) {
      var configurationNode = section.querySelector(".player-configuration");
      try {
        var configuration = JSON.parse(configurationNode.textContent);
        players.push(new ComparisonPlayer(section, configuration));
      } catch (error) {
        var status = section.querySelector(".player-status");
        if (status) { status.textContent = "The player could not start: " + error.message; status.className = "player-status is-error"; }
        scriptErrors.push("player: " + error.message);
        root.setAttribute("data-script-errors", scriptErrors.join(" | "));
      }
    });
    root.setAttribute("data-players-ready", String(players.length));
  }

  function start() {
    markCurrentSection();
    setUpFigureOverlay();
    setUpPlayers();
    root.setAttribute("data-page-ready", "true");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
