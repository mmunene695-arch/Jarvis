(function () {
  let allLeads = [];
  let activeStage = "All";

  const STAGES = [
    "Ready to Call",
    "Queued",
    "Called - Demo Sent",
    "Follow-Up Staged",
    "Negotiating",
    "Deposit Paid",
    "Delivered / Retainer",
    "Inbound Web",
    "Paused - Bounced",
    "Lost",
  ];

  function stagePillClass(stage) {
    if (stage === "Deposit Paid" || stage === "Delivered / Retainer") return "pill-green";
    if (stage === "Ready to Call" || stage === "Negotiating") return "pill-amber";
    if (stage === "Paused - Bounced" || stage === "Lost") return "pill-red";
    return "pill-blue";
  }

  function kes(val) {
    return "KES " + Number(val || 0).toLocaleString();
  }

  async function refreshAll() {
    try {
      const [ovRes, leadsRes, decRes] = await Promise.all([
        fetch("./api/overview"),
        fetch("./api/leads"),
        fetch("./api/decisions"),
      ]);
      if (!ovRes.ok) throw new Error("Backend offline");
      const ov = await ovRes.json();
      const leadsData = await leadsRes.json();
      const decData = await decRes.json();

      const m = ov.metrics;
      document.getElementById("kpi-local-pipe").textContent = kes(m.local_pipeline_kes);
      document.getElementById("kpi-ready-count").textContent = `${m.ready_to_call} ready to dial right now`;
      document.getElementById("kpi-proj-cash").textContent = kes(m.projected_14d_cash_kes);
      document.getElementById("kpi-collected").textContent = kes(m.collected_deposits_kes);
      document.getElementById("kpi-mrr").textContent = `Potential local MRR: ${kes(m.potential_local_mrr_kes)}/mo`;
      document.getElementById("kpi-mid-pipe").textContent = kes(m.midmarket_pipeline_kes);

      allLeads = leadsData.leads || [];
      renderLeads();
      renderDecisions(decData.decisions || []);
    } catch (_err) {
      try {
        const res = await fetch("./static_data/bootstrap.json");
        const snap = await res.json();
        allLeads = (snap.leads || []).map((l, idx) => Object.assign({ id: idx + 1, deposit_paid_kes: 0 }, l));
        renderLeads();
        renderDecisions(snap.decisions || []);
      } catch (_e2) {
        // ignore
      }
    }
  }

  function renderLeads() {
    const tbody = document.getElementById("crm-tbody");
    if (!tbody) return;
    const filtered = activeStage === "All" ? allLeads : allLeads.filter((l) => l.stage === activeStage);

    tbody.innerHTML = filtered
      .map((lead) => {
        const options = STAGES.map(
          (s) => `<option value="${s}" ${s === lead.stage ? "selected" : ""}>${s}</option>`
        ).join("");
        const priceHtml =
          lead.ask_kes > 0
            ? `<strong>${kes(lead.ask_kes)}</strong><br/><span style="font-size:0.78rem; color:var(--text-muted);">Accept ${kes(lead.accept_kes)} · Floor ${kes(lead.floor_kes)}<br/>+${kes(lead.retainer_kes)}/mo care</span>`
            : `<span style="color:var(--text-muted);">Quarantined</span>`;
        return `
          <tr>
            <td>
              <strong style="font-size:0.95rem; color:#fff;">${lead.company}</strong><br/>
              <span style="font-size:0.8rem; color:var(--text-muted);">${lead.contact_name || ""} · ${lead.location || ""}</span><br/>
              <span style="font-size:0.82rem; color:#6ee7b7;">${lead.phone || lead.email || ""}</span>
            </td>
            <td>
              <span class="pill ${stagePillClass(lead.stage)}">${lead.stage}</span><br/>
              <select data-lead-stage="${lead.id}" style="margin-top:8px; background:#091512; color:#fff; border:1px solid var(--border); border-radius:6px; padding:4px 6px; font-size:0.78rem;">
                ${options}
              </select>
            </td>
            <td>${priceHtml}</td>
            <td style="max-width:340px;">
              <div style="font-size:0.82rem; margin-bottom:6px;">${lead.pain_point}</div>
              <div style="font-size:0.79rem; color:#fcd34d;"><strong>Next:</strong> ${lead.next_action}</div>
            </td>
            <td>
              <div style="display:flex; flex-direction:column; gap:6px;">
                <button type="button" class="btn btn-primary btn-sm" data-pitch-id="${lead.id}">Pitch &amp; Invoice</button>
                <a href=".${lead.demo_path}" target="_blank" class="btn btn-outline btn-sm">Open Demo ↗</a>
              </div>
            </td>
          </tr>
        `;
      })
      .join("");

    tbody.querySelectorAll("[data-lead-stage]").forEach((sel) => {
      sel.addEventListener("change", async (ev) => {
        const id = Number(ev.target.getAttribute("data-lead-stage"));
        const newStage = ev.target.value;
        try {
          await fetch(`./api/leads/${id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ stage: newStage }),
          });
          await refreshAll();
        } catch (_e) {
          const item = allLeads.find((x) => x.id === id);
          if (item) item.stage = newStage;
          renderLeads();
        }
      });
    });

    tbody.querySelectorAll("[data-pitch-id]").forEach((btn) => {
      btn.addEventListener("click", () => openPitchModal(Number(btn.getAttribute("data-pitch-id"))));
    });
  }

  function renderDecisions(decisions) {
    const box = document.getElementById("decisions-list");
    if (!box) return;
    box.innerHTML = decisions
      .map(
        (d) => `
        <article class="card">
          <div>
            <div style="display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom:8px;">
              <span class="badge">${d.code} · ${d.category}</span>
              <span class="pill pill-green">${d.status}</span>
            </div>
            <h3 style="margin:0 0 10px;">${d.title}</h3>
            <p style="font-size:0.88rem; color:#fca5a5; margin:0 0 8px;"><strong>Issue Identified:</strong> ${d.issue_found}</p>
            <p style="font-size:0.88rem; color:var(--text); margin:0 0 8px;"><strong>Executive Decision:</strong> ${d.decision_made}</p>
            <p style="font-size:0.86rem; color:#6ee7b7; margin:0;"><strong>Business Impact:</strong> ${d.impact}</p>
          </div>
        </article>
      `
      )
      .join("");
  }

  async function openPitchModal(leadId) {
    let bundle = null;
    try {
      const res = await fetch("./api/pitch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lead_id: leadId }),
      });
      if (res.ok) bundle = await res.json();
    } catch (_err) {
      // fallback below
    }

    if (!bundle) {
      const lead = allLeads.find((x) => x.id === leadId) || allLeads[0];
      const q = lead.ask_kes || 45000;
      bundle = {
        invoice_number: "KF-2026-101",
        lead: lead,
        package_name: "7-Day Mobile & WhatsApp Conversion Sprint",
        quote_kes: q,
        deposit_kes: Math.floor(q / 2),
        balance_kes: q - Math.floor(q / 2),
        retainer_kes: lead.retainer_kes || 5000,
        valid_until: "2026-11-13",
        call_opener: `Morning! My name's Mark Munene from KiboFlow Studio here in Nyeri — I built a mobile website concept for ${lead.company} and I'd love to send it on WhatsApp.`,
        whatsapp_message: `Hi, Mark Munene here. Open this live mobile concept on your phone:\n{ORIGIN}${lead.demo_path}`,
        scope_protection_line: `Ask: KES ${q.toLocaleString()} | Accept: KES ${(lead.accept_kes || 38000).toLocaleString()} (smaller scope) | Floor: KES ${(lead.floor_kes || 32000).toLocaleString()}`,
      };
    }

    const origin = window.location.origin;
    const waText = bundle.whatsapp_message.replace("{ORIGIN}", origin);

    document.getElementById("modal-lead-title").textContent = `${bundle.lead.company} — Pitch & Deposit Invoice`;
    document.getElementById("modal-call-script").textContent = bundle.call_opener;
    document.getElementById("modal-wa-script").textContent = waText;
    document.getElementById("modal-floor-rule").textContent = bundle.scope_protection_line;

    document.getElementById("inv-number").textContent = `INVOICE #${bundle.invoice_number}`;
    document.getElementById("inv-valid").textContent = `Slot & Price Held Until ${bundle.valid_until}`;
    document.getElementById("inv-client").textContent = `${bundle.lead.company} (${bundle.lead.location || "Kenya"})`;
    document.getElementById("inv-pkg").textContent = bundle.package_name;
    document.getElementById("inv-deposit").textContent = kes(bundle.deposit_kes);
    document.getElementById("inv-balance").textContent = kes(bundle.balance_kes);
    document.getElementById("inv-total").textContent = kes(bundle.quote_kes);
    document.getElementById("inv-retainer").textContent = kes(bundle.retainer_kes);

    const digits = (bundle.lead.phone || "").replace(/[^0-9]/g, "");
    const targetPhone = digits.length >= 9 ? digits : "254729213641";
    document.getElementById("open-wa-direct").href =
      `https://wa.me/${targetPhone}?text=${encodeURIComponent(waText)}`;

    document.getElementById("copy-wa-btn").onclick = () => {
      navigator.clipboard?.writeText(waText);
      document.getElementById("copy-wa-btn").textContent = "Copied!";
      setTimeout(() => {
        document.getElementById("copy-wa-btn").textContent = "Copy WhatsApp Message";
      }, 1600);
    };

    document.getElementById("pitch-modal").classList.add("open");
  }

  document.getElementById("close-pitch-modal")?.addEventListener("click", () => {
    document.getElementById("pitch-modal").classList.remove("open");
  });

  document.getElementById("open-new-lead-btn")?.addEventListener("click", () => {
    document.getElementById("new-lead-modal").classList.add("open");
  });

  document.getElementById("close-new-lead-modal")?.addEventListener("click", () => {
    document.getElementById("new-lead-modal").classList.remove("open");
  });

  document.getElementById("new-lead-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const sectorRaw = document.getElementById("nl-sector").value.trim() || "Nyeri · SMB";
    const parts = sectorRaw.split("·").map((s) => s.trim());
    const payload = {
      company: document.getElementById("nl-company").value.trim(),
      contact_name: document.getElementById("nl-contact").value.trim(),
      phone: document.getElementById("nl-phone").value.trim(),
      location: parts[0] || "Nyeri",
      sector: parts[1] || "Local SMB",
      track: "Local Fast-Cash",
      stage: "Ready to Call",
      priority: 1,
      ask_kes: Number(document.getElementById("nl-ask").value || 45000),
      pain_point: document.getElementById("nl-pain").value.trim() || "Needs mobile conversion & WhatsApp booking funnel",
      next_action: "Call & send live mobile concept via WhatsApp",
    };
    try {
      await fetch("./api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (_err) {
      allLeads.unshift(Object.assign({ id: Date.now(), accept_kes: 38000, floor_kes: 32000, retainer_kes: 5000, demo_path: "/demos/hospitality" }, payload));
    }
    document.getElementById("new-lead-modal").classList.remove("open");
    e.target.reset();
    await refreshAll();
  });

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const target = btn.getAttribute("data-tab");
      ["tab-crm", "tab-decisions", "tab-systems"].forEach((id) => {
        document.getElementById(id).style.display = id === target ? "block" : "none";
      });
    });
  });

  document.querySelectorAll(".stage-filter").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".stage-filter").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeStage = btn.getAttribute("data-stage");
      renderLeads();
    });
  });

  refreshAll();
})();
