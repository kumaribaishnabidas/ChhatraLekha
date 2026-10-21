/* EduSynC credential verification page. */
(function () {
  'use strict';

  const api = window.EduSync.api;
  const escapeHtml = window.EduSync.escapeHtml;

  const tabs = Array.from(document.querySelectorAll('.tab'));
  const panelId = document.getElementById('panel-id');
  const panelScan = document.getElementById('panel-scan');
  const form = document.getElementById('verify-form');
  const errorBox = document.getElementById('verify-error');
  const resultBox = document.getElementById('result');

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      tabs.forEach(function (other) { other.classList.remove('active'); });
      tab.classList.add('active');
      const mode = tab.dataset.mode;
      panelId.hidden = mode !== 'id';
      panelScan.hidden = mode !== 'scan';
    });
  });

  function verdictClass(verdict) {
    if (verdict === 'VALID') return 'VERIFIED';
    if (verdict === 'NOT_FOUND' || verdict === 'REVOKED' || verdict === 'INVALID') return 'FLAGGED_ANOMALY';
    return 'PENDING_REVIEW';
  }

  function render(result) {
    resultBox.hidden = false;
    resultBox.innerHTML = '';

    const card = document.createElement('div');
    card.className = 'card';

    const header = document.createElement('div');
    header.className = 'pill-row';
    header.style.marginBottom = '12px';

    const badge = document.createElement('span');
    badge.className = 'badge ' + verdictClass(result.verdict);
    badge.textContent = result.verdict;
    header.appendChild(badge);

    const apaar = document.createElement('span');
    apaar.className = 'mono';
    apaar.textContent = 'APAAR ' + result.apaar_id;
    header.appendChild(apaar);
    card.appendChild(header);

    const heading = document.createElement('h2');
    heading.textContent = result.verified ? 'Credential verified' : 'Credential could not be verified';
    card.appendChild(heading);

    const reason = document.createElement('p');
    reason.textContent = result.reason || '';
    card.appendChild(reason);

    if (result.consent_note) {
      const consent = document.createElement('p');
      consent.className = 'hint';
      consent.style.marginTop = '8px';
      consent.textContent = 'Consent: ' + result.consent_note;
      card.appendChild(consent);
    }

    if (result.student) {
      const hr = document.createElement('hr');
      hr.className = 'sep';
      card.appendChild(hr);

      const table = document.createElement('table');
      const rows = [
        ['Student', result.student.student_name],
        ['Institution', result.institution_name || result.student.institution_id],
        ['Programme', result.program_name || result.student.program_id],
        ['Academic year', result.student.academic_year],
        ['Quota', result.student.admission_quota],
        ['Roll number', result.student.student_institute_roll_no],
        ['Verification status', result.student.verification_status]
      ];
      rows.forEach(function (pair) {
        const tr = document.createElement('tr');
        const th = document.createElement('th');
        th.textContent = pair[0];
        const td = document.createElement('td');
        td.textContent = pair[1] || '-';
        tr.appendChild(th);
        tr.appendChild(td);
        table.appendChild(tr);
      });
      card.appendChild(table);
    } else if (result.student === null) {
      const withheld = document.createElement('p');
      withheld.className = 'hint';
      withheld.style.marginTop = '10px';
      withheld.textContent = 'Personal details are withheld: the student has not consented to credential verification.';
      card.appendChild(withheld);
    }

    if (result.anomalies && result.anomalies.length) {
      const hr = document.createElement('hr');
      hr.className = 'sep';
      card.appendChild(hr);
      const title = document.createElement('h3');
      title.textContent = 'Anomalies on this record (' + result.anomalies.length + ')';
      card.appendChild(title);

      const list = document.createElement('ul');
      result.anomalies.forEach(function (anomaly) {
        const li = document.createElement('li');
        const severity = document.createElement('span');
        severity.className = 'badge ' + anomaly.severity;
        severity.textContent = anomaly.severity;
        li.appendChild(severity);
        li.appendChild(document.createTextNode(' ' + escapeHtml(anomaly.details)));
        list.appendChild(li);
      });
      card.appendChild(list);
    }

    resultBox.appendChild(card);
  }

  async function verify(apaarId, seal) {
    errorBox.hidden = true;
    let path = '/api/verify/' + encodeURIComponent(apaarId);
    if (seal) {
      path += '?seal=' + encodeURIComponent(seal);
    }
    const response = await api(path);
    const payload = await response.json();
    if (!response.ok) {
      errorBox.textContent = payload.detail || 'Verification failed.';
      errorBox.hidden = false;
      return;
    }
    render(payload);
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    const value = document.getElementById('apaar').value.replace(/\D/g, '');
    if (value.length !== 12) {
      errorBox.textContent = 'An APAAR ID is exactly 12 digits.';
      errorBox.hidden = false;
      return;
    }
    verify(value, null);
  });

  // --------------------------------------------------------------- camera

  const video = document.getElementById('scan-video');
  const scanStatus = document.getElementById('scan-status');
  const startButton = document.getElementById('scan-start');
  const stopButton = document.getElementById('scan-stop');
  const uploadButton = document.getElementById('scan-upload');
  const fileInput = document.getElementById('scan-file');
  let stream = null;
  let raf = null;

  function stopCamera() {
    if (raf) {
      cancelAnimationFrame(raf);
      raf = null;
    }
    if (stream) {
      stream.getTracks().forEach(function (track) { track.stop(); });
      stream = null;
    }
    video.srcObject = null;
    startButton.hidden = false;
    stopButton.hidden = true;
  }

  function detectFrame() {
    if (!window.BarcodeDetector) return;
    const detector = new window.BarcodeDetector({ formats: ['qr_code'] });
    const tick = async function () {
      if (!stream) return;
      try {
        const codes = await detector.detect(video);
        if (codes && codes.length) {
          const raw = codes[0].rawValue;
          stopCamera();
          const parsed = parsePayload(raw);
          verify(parsed.apaar, parsed.seal);
          return;
        }
      } catch (error) {
        /* keep scanning */
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
  }

  function parsePayload(raw) {
    try {
      const url = new URL(raw, window.location.origin);
      const params = url.searchParams;
      return {
        apaar: (params.get('apaar') || raw.replace(/\D/g, '')).replace(/\D/g, ''),
        seal: params.get('seal')
      };
    } catch (error) {
      return { apaar: raw.replace(/\D/g, ''), seal: null };
    }
  }

  startButton.addEventListener('click', async function () {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      scanStatus.textContent = 'This browser does not expose a camera. Use the image upload instead.';
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      video.srcObject = stream;
      await video.play();
      startButton.hidden = true;
      stopButton.hidden = false;
      scanStatus.textContent = 'Point the camera at the APAAR QR badge.';
      if (window.BarcodeDetector) {
        detectFrame();
      } else {
        scanStatus.textContent = 'This browser has no Barcode Detection API. Use the image upload instead.';
      }
    } catch (error) {
      scanStatus.textContent = 'Camera access was refused. Use the image upload instead.';
    }
  });

  stopButton.addEventListener('click', stopCamera);
  uploadButton.addEventListener('click', function () { fileInput.click(); });

  fileInput.addEventListener('change', function () {
    const file = fileInput.files && fileInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function () {
      if (window.jsQR) {
        const image = new Image();
        image.onload = function () {
          const canvas = document.createElement('canvas');
          canvas.width = image.width;
          canvas.height = image.height;
          const context = canvas.getContext('2d');
          context.drawImage(image, 0, 0);
          const data = context.getImageData(0, 0, canvas.width, canvas.height);
          const code = window.jsQR(data.data, data.width, data.height);
          if (!code) {
            scanStatus.textContent = 'No QR code was found in that image.';
            return;
          }
          const parsed = parsePayload(code.data);
          verify(parsed.apaar, parsed.seal);
        };
        image.src = reader.result;
      } else {
        scanStatus.textContent = 'The QR decoding library is not loaded.';
      }
    };
    reader.readAsDataURL(file);
  });

  // Pre-fill from a deep link and verify straight away.
  const initial = document.getElementById('apaar').value.replace(/\D/g, '');
  if (initial.length === 12) {
    verify(initial, null);
  }
})();
