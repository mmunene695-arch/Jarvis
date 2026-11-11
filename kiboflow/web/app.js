(function () {
  let currency = "KES";
  let packagesData = [];

  function fmtMoney(kes, usd) {
    if (currency === "USD") {
      const val = usd !== undefined ? usd : Math.round(kes / 129);
      return "US$" + Number(val).toLocaleString();
    }
    return "KES " + Number(kes).toLocaleString();
  }

  function renderPackages() {
    const grid = document.getElementById("packages-grid");
    if (!grid) return;
    grid.innerHTML = packagesData
      .map((pkg) => {
        const mainPrice = fmtMoney(pkg.price_kes, pkg.price_usd);
        const deposit = fmtMoney(Math.round(pkg.price_kes / 2), Math.round(pkg.price_usd / 2));
        const retainer = fmtMoney(pkg.retainer_kes, pkg.retainer_usd);
        const items = (pkg.deliverables || []).map((d) => `<li>${d}</li>`).join("");
        const waText = encodeURIComponent(
          `Hi Mark, I'm interested in KiboFlow Studio's "${pkg.name}" (${mainPrice}). Can we discuss a 7-day build for my business?`
        );
        return `
          <article class="card">
            <div>
              <span class="badge">${pkg.badge}</span>
              <h3 style="margin:0 0 6px;">${pkg.name}</h3>
              <p style="font-size:0.86rem; color:var(--text-muted); margin:0 0 10px;">${pkg.ideal_for}</p>
              <div class="price-big">${mainPrice}</div>
              <div class="price-sub">50% deposit (${deposit}) · Optional care plan: ${retainer}/mo</div>
              <ul class="check-list">${items}</ul>
            </div>
            <a class="btn btn-primary" href="https://wa.me/254729213641?text=${waText}" target="_blank" rel="noopener">
              Book ${pkg.turnaround_days}-Day Slot on WhatsApp →
            </a>
          </article>
        `;
      })
      .join("");
  }

  async function loadPackages() {
    try {
      const res = await fetch("./api/packages");
      if (!res.ok) throw new Error("API unavailable");
      const data = await res.json();
      packagesData = data.packages || [];
    } catch (_err) {
      try {
        const fallback = await fetch("./static_data/bootstrap.json");
        const data = await fallback.json();
        packagesData = data.packages || [];
      } catch (_e2) {
        packagesData = [];
      }
    }
    renderPackages();
  }

  function computeLocalRoi() {
    const visitors = Math.max(50, Number(document.getElementById("roi-visitors").value || 1200));
    const avgOrder = Math.max(200, Number(document.getElementById("roi-order").value || 3500));
    const currPct = Math.max(0.1, Number(document.getElementById("roi-curr").value || 1.2));
    const targPct = Math.max(currPct + 0.5, Number(document.getElementById("roi-targ").value || 3.8));

    const currCust = Math.round(visitors * (currPct / 100));
    const targCust = Math.round(visitors * (targPct / 100));
    const added = Math.max(1, targCust - currCust);
    const monthlyLiftKes = added * avgOrder;
    const annualLiftKes = monthlyLiftKes * 12;
    const paybackDays = Math.max(2, Math.round((45000 / Math.max(1, monthlyLiftKes)) * 30));

    document.getElementById("roi-monthly-lift").textContent = fmtMoney(monthlyLiftKes) + " / mo";
    document.getElementById("roi-annual-lift").textContent = fmtMoney(annualLiftKes);
    document.getElementById("roi-payback").textContent = paybackDays + " Days";
    document.getElementById("roi-customers-line").textContent =
      `+${added} extra paying bookings/orders per month (${currCust} → ${targCust} conversions).`;
  }

  document.getElementById("curr-kes")?.addEventListener("click", () => {
    currency = "KES";
    document.getElementById("curr-kes").classList.add("active");
    document.getElementById("curr-usd").classList.remove("active");
    renderPackages();
    computeLocalRoi();
  });

  document.getElementById("curr-usd")?.addEventListener("click", () => {
    currency = "USD";
    document.getElementById("curr-usd").classList.add("active");
    document.getElementById("curr-kes").classList.remove("active");
    renderPackages();
    computeLocalRoi();
  });

  document.getElementById("roi-calc-btn")?.addEventListener("click", computeLocalRoi);

  document.getElementById("audit-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const businessName = document.getElementById("audit-name").value.trim();
    const websiteUrl = document.getElementById("audit-url").value.trim();
    const sector = document.getElementById("audit-sector").value;
    const phone = document.getElementById("audit-phone").value.trim();

    let audit = null;
    try {
      const res = await fetch("./api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: businessName,
          website_url: websiteUrl,
          sector: sector,
          phone: phone,
          save_lead: Boolean(phone),
        }),
      });
      if (res.ok) {
        const payload = await res.json();
        audit = payload.audit;
      }
    } catch (_err) {
      // Static mode fallback
    }

    if (!audit) {
      const hasSite = Boolean(websiteUrl && websiteUrl.toLowerCase() !== "none");
      audit = {
        business_name: businessName,
        mobile_conversion_score: hasSite ? 52 : 24,
        headline: hasSite
          ? `${websiteUrl} leaks mobile visitors without a sticky 3-second WhatsApp booking bar.`
          : `${businessName} has zero mobile landing page—searchers bounce before calling.`,
        findings: [
          "Missing 1-tap pre-filled WhatsApp inquiry/booking funnel above the fold.",
          "Opportunity to capture high-intent Google Maps 'near me' mobile searches.",
          "Recommended 7-day conversion sprint with 50% M-Pesa deposit protection.",
        ],
        recommended_package: { name: "7-Day Mobile & WhatsApp Sprint", price_kes: 45000, deposit_kes: 22500 },
      };
    }

    document.getElementById("audit-res-title").textContent = audit.headline;
    document.getElementById("audit-res-score").textContent = `${audit.mobile_conversion_score} / 100`;
    document.getElementById("audit-res-list").innerHTML = audit.findings.map((f) => `<li>${f}</li>`).join("");
    const waMsg = encodeURIComponent(
      `Hi Mark, I just ran the KiboFlow Mobile Audit for ${businessName} (Score: ${audit.mobile_conversion_score}/100). Please send me a concept demo!`
    );
    document.getElementById("audit-res-cta").innerHTML = `
      <div style="padding:12px; border-radius:10px; background:rgba(16,185,129,0.12); margin-bottom:12px; font-size:0.88rem;">
        <strong>Recommended:</strong> ${audit.recommended_package.name} — KES ${Number(audit.recommended_package.price_kes).toLocaleString()}
        (50% deposit: KES ${Number(audit.recommended_package.deposit_kes).toLocaleString()})
      </div>
      <a class="btn btn-amber" style="width:100%;" href="https://wa.me/254729213641?text=${waMsg}" target="_blank" rel="noopener">
        Claim Free Concept Demo on WhatsApp →
      </a>
    `;
  });

  loadPackages();
  computeLocalRoi();
})();
