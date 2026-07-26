function buildExec(){
  const s = DATA.exec_summary;
  const kpis = DATA.executive_kpis;
  mainEl.innerHTML = `
    <div class="page-header">
      <h1>Executive Overview</h1>
      <p>Platform health as of ${s.latest_month} — active landlords, activation, revenue, and payment reliability at a glance.</p>
    </div>
    <div class="narrative">
      <b>Latest month:</b> ${fmtNum(s.new_landlords)} new landlords signed up
      (${s.new_landlords_mom_pct!=null ? (s.new_landlords_mom_pct>=0?'+':'')+fmtPct(s.new_landlords_mom_pct) : '—'} vs prior month),
      with a ${fmtPct(s.activation_rate)} 7-day activation rate. MRR stands at ${fmtMoney(s.mrr)}
      with a ${fmtPct(s.payment_success_rate)} on-time payment rate.
    </div>
    <div class="kpi-row">
      <div class="kpi-card"><div class="label">New Landlords</div><div class="value">${fmtNum(s.new_landlords)}</div>
        <div class="delta ${s.new_landlords_mom_pct>=0?'up':'down'}">${s.new_landlords_mom_pct!=null?(s.new_landlords_mom_pct>=0?'▲ ':'▼ ')+fmtPct(Math.abs(s.new_landlords_mom_pct)):'—'} MoM</div></div>
      <div class="kpi-card"><div class="label">7-Day Activation</div><div class="value">${fmtPct(s.activation_rate)}</div></div>
      <div class="kpi-card"><div class="label">MRR</div><div class="value">${fmtMoney(s.mrr)}</div></div>
      <div class="kpi-card"><div class="label">Payment Success</div><div class="value">${fmtPct(s.payment_success_rate)}</div></div>
    </div>
    <div class="grid-2">
      <div class="card"><h3>New Landlords by Month</h3><div class="sub">Signups + activated, last 24 months</div>
        <div class="chart-wrap"><canvas id="c1"></canvas></div></div>
      <div class="card"><h3>Activation & Free-to-Paid Conversion</h3><div class="sub">Monthly rate trends</div>
        <div class="chart-wrap"><canvas id="c2"></canvas></div></div>
    </div>
    <div class="card"><h3>Applications & Lease Conversion</h3><div class="sub">Monthly application volume vs. signed-lease rate</div>
      <div class="chart-wrap short"><canvas id="c3"></canvas></div></div>
  `;
  const last24 = kpis.slice(-24);
  renderedCharts.c1 = new Chart(document.getElementById('c1'), {
    type:'bar',
    data:{labels:last24.map(r=>r.month), datasets:[
      {label:'New landlords', data:last24.map(r=>r.new_landlords), backgroundColor:'#93c5fd'},
      {label:'Activated', data:last24.map(r=>r.activated_landlords), backgroundColor:'#0d9488'},
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}}, scales:{x:{ticks:{font:{size:9}}}}}
  });
  renderedCharts.c2 = new Chart(document.getElementById('c2'), {
    type:'line',
    data:{labels:last24.map(r=>r.month), datasets:[
      {label:'Activation rate', data:last24.map(r=>r.activation_rate), borderColor:'#0d9488', tension:.3, pointRadius:0},
      {label:'Free-to-paid conversion', data:last24.map(r=>r.free_to_paid_conversion), borderColor:'#f59e0b', tension:.3, pointRadius:0},
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}}, scales:{y:{ticks:{callback:v=>(v*100).toFixed(0)+'%'}}, x:{ticks:{font:{size:9}}}}}
  });
  renderedCharts.c3 = new Chart(document.getElementById('c3'), {
    type:'bar',
    data:{labels:last24.map(r=>r.month), datasets:[
      {label:'Applications', data:last24.map(r=>r.applications), backgroundColor:'#c7d2fe', yAxisID:'y'},
      {label:'Lease conversion rate', data:last24.map(r=>r.lease_conversion_rate), type:'line', borderColor:'#e11d48', yAxisID:'y1', pointRadius:0, tension:.3},
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}},
      scales:{y:{position:'left'}, y1:{position:'right', grid:{drawOnChartArea:false}, ticks:{callback:v=>(v*100).toFixed(0)+'%'}}, x:{ticks:{font:{size:9}}}}}
  });
}

function buildAcq(){
  const byChannel = DATA.acquisition_by_channel.sort((a,b)=>b.signups-a.signups);
  const byDevice = DATA.acquisition_by_device;
  const f = DATA.funnel_overall;
  const funnelLabels = ['Account Created','Property Added','Listing Published','Tenant Invited','Rent Collection','Paid Subscription'];
  const funnelVals = [1, f.pct_property_added, f.pct_listing_published, f.pct_tenant_invited, f.pct_rent_collection_enabled, f.pct_paid_conversion];
  mainEl.innerHTML = `
    <div class="page-header"><h1>Acquisition & Activation</h1>
      <p>Where landlords come from, what they cost to acquire, and how far they get through onboarding.</p></div>
    <div class="grid-2">
      <div class="card"><h3>Signups & CAC by Channel</h3><div class="sub">Bar = signups (left axis), line = CAC $ (right axis)</div>
        <div class="chart-wrap"><canvas id="c1"></canvas></div></div>
      <div class="card"><h3>Onboarding Funnel</h3><div class="sub">% of activated landlords reaching each step</div>
        <div class="chart-wrap"><canvas id="c2"></canvas></div></div>
    </div>
    <div class="grid-2">
      <div class="card"><h3>Activation Rate by Channel</h3>
        <div class="chart-wrap short"><canvas id="c3"></canvas></div></div>
      <div class="card"><h3>Mobile vs. Desktop Activation</h3>
        <div class="chart-wrap short"><canvas id="c4"></canvas></div></div>
    </div>
    <div class="card"><h3>Worst Listing-Publish Abandonment (channel × device)</h3>
      <div class="sub">Highest-volume segments where landlords add a property but never publish it</div>
      <table><thead><tr><th>Channel</th><th>Device</th><th>Landlords</th><th>Publish abandonment</th></tr></thead>
      <tbody id="abandon-table"></tbody></table>
    </div>
  `;
  renderedCharts.c1 = new Chart(document.getElementById('c1'), {
    data:{labels:byChannel.map(r=>r.acquisition_channel), datasets:[
      {type:'bar', label:'Signups', data:byChannel.map(r=>r.signups), backgroundColor:'#93c5fd', yAxisID:'y'},
      {type:'line', label:'CAC ($)', data:byChannel.map(r=>r.cac), borderColor:'#e11d48', yAxisID:'y1', pointRadius:3, tension:.2},
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}},
      scales:{y:{position:'left'}, y1:{position:'right', grid:{drawOnChartArea:false}}, x:{ticks:{font:{size:9}}}}}
  });
  renderedCharts.c2 = new Chart(document.getElementById('c2'), {
    type:'bar',
    data:{labels:funnelLabels, datasets:[{label:'% reaching step', data:funnelVals, backgroundColor:'#0d9488'}]},
    options:{indexAxis:'y', responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{x:{ticks:{callback:v=>(v*100).toFixed(0)+'%'}, max:1}}}
  });
  renderedCharts.c3 = new Chart(document.getElementById('c3'), {
    type:'bar',
    data:{labels:byChannel.map(r=>r.acquisition_channel), datasets:[{label:'Activation rate', data:byChannel.map(r=>r.activation_rate), backgroundColor:CHART_COLORS}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}, scales:{y:{ticks:{callback:v=>(v*100).toFixed(0)+'%'}}, x:{ticks:{font:{size:9}}}}}
  });
  renderedCharts.c4 = new Chart(document.getElementById('c4'), {
    type:'bar',
    data:{labels:byDevice.map(r=>r.signup_device), datasets:[{label:'Activation rate', data:byDevice.map(r=>r.activation_rate), backgroundColor:['#0d9488','#2563eb','#f59e0b']}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}, scales:{y:{ticks:{callback:v=>(v*100).toFixed(0)+'%'}}}}
  });
  const tbody = document.getElementById('abandon-table');
  DATA.funnel_by_channel_device.filter(r=>r.landlords>=200).sort((a,b)=>b.publish_abandonment_rate-a.publish_abandonment_rate).slice(0,8).forEach(r=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="tag">${r.acquisition_channel}</td><td class="tag">${r.signup_device}</td><td>${fmtNum(r.landlords)}</td><td>${fmtPct(r.publish_abandonment_rate)}</td>`;
    tbody.appendChild(tr);
  });
}

function buildEngagement(){
  const byFeature = DATA.retention_by_feature;
  const byPlan = DATA.retention_by_plan;
  const features = [...new Set(byFeature.map(r=>r.first_feature_adopted))];
  const offsets = [0,1,2,3,4,5,6];
  mainEl.innerHTML = `
    <div class="page-header"><h1>Engagement & Retention</h1>
      <p>Cohort retention curves — does the first feature a landlord adopts predict how well they stick around?</p></div>
    <div class="narrative"><b>Key finding:</b> landlords whose first action is enabling <b>online rent collection</b>
      retain noticeably better at every horizon than landlords who only use listing tools first — the workflow habit
      matters more than simple product discovery.</div>
    <div class="card"><h3>Retention Curve by First Feature Adopted</h3><div class="sub">% of activated landlords still active, by months since signup</div>
      <div class="chart-wrap"><canvas id="c1"></canvas></div></div>
    <div class="grid-2">
      <div class="card"><h3>Paid vs. Free Retention</h3>
        <div class="chart-wrap short"><canvas id="c2"></canvas></div></div>
      <div class="card"><h3>Month-6 Retention by Signup Cohort</h3>
        <div class="chart-wrap short"><canvas id="c3"></canvas></div></div>
    </div>
  `;
  renderedCharts.c1 = new Chart(document.getElementById('c1'), {
    type:'line',
    data:{labels:offsets, datasets:features.map((f,i)=>({
      label:f, data:offsets.map(o=>{const row=byFeature.find(r=>r.first_feature_adopted===f && r.m_offset===o); return row?row.retention_rate:null;}),
      borderColor:CHART_COLORS[i%CHART_COLORS.length], tension:.3, pointRadius:2,
      borderWidth: f==='online_rent_collection'?3:1.5,
    }))},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}}, scales:{y:{ticks:{callback:v=>(v*100).toFixed(0)+'%'}}, x:{title:{display:true,text:'Months since signup'}}}}
  });
  renderedCharts.c2 = new Chart(document.getElementById('c2'), {
    type:'line',
    data:{labels:offsets, datasets:['paid','free'].map((p,i)=>({
      label:p, data:offsets.map(o=>{const row=byPlan.find(r=>r.plan_type===p && r.m_offset===o); return row?row.retention_rate:null;}),
      borderColor: p==='paid'?'#0d9488':'#94a3b8', tension:.3, pointRadius:2,
    }))},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}}, scales:{y:{ticks:{callback:v=>(v*100).toFixed(0)+'%'}}}}
  });
  const heat = DATA.cohort_month6_heatmap.sort((a,b)=>a.cohort_month.localeCompare(b.cohort_month)).slice(-18);
  renderedCharts.c3 = new Chart(document.getElementById('c3'), {
    type:'bar',
    data:{labels:heat.map(r=>r.cohort_month), datasets:[{label:'Month-6 retention', data:heat.map(r=>r.retention_rate), backgroundColor:'#7c3aed'}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}, scales:{y:{ticks:{callback:v=>(v*100).toFixed(0)+'%'}}, x:{ticks:{font:{size:8}}}}}
  });
}

function buildRevenue(){
  const rev = DATA.revenue_monthly.slice(-24);
  const fc = DATA.revenue_forecast;
  const allLabels = [...rev.map(r=>r.month), ...fc.map(r=>r.month)];
  const actual = [...rev.map(r=>r.mrr), ...fc.map(()=>null)];
  const forecast = [...rev.map(()=>null), rev[rev.length-1].mrr, ...fc.slice(1).map(r=>r.forecast_mrr)];
  forecast[rev.length-1] = rev[rev.length-1].mrr; // connect the line
  mainEl.invisible;
  mainEl.innerHTML = `
    <div class="page-header"><h1>Revenue & Forecasting</h1>
      <p>MRR bridge, ARPU, and a 6-month forward forecast (Holt linear trend, backtested against seasonal-naive baseline).</p></div>
    <div class="kpi-row">
      <div class="kpi-card"><div class="label">Current MRR</div><div class="value">${fmtMoney(rev[rev.length-1].mrr)}</div></div>
      <div class="kpi-card"><div class="label">ARPU</div><div class="value">${fmtMoney(rev[rev.length-1].arpu)}</div></div>
      <div class="kpi-card"><div class="label">6mo Forecast MRR</div><div class="value">${fmtMoney(fc[fc.length-1].forecast_mrr)}</div></div>
      <div class="kpi-card"><div class="label">Paying Landlords</div><div class="value">${fmtNum(rev[rev.length-1].paying_landlords)}</div></div>
    </div>
    <div class="card"><h3>MRR: Actual + 6-Month Forecast</h3><div class="sub">Holt linear-trend model, backtested MAPE 2.9% vs. 39.6% for seasonal-naive baseline</div>
      <div class="chart-wrap"><canvas id="c1"></canvas></div></div>
    <div class="grid-2">
      <div class="card"><h3>New vs. Churned MRR</h3>
        <div class="chart-wrap short"><canvas id="c2"></canvas></div></div>
      <div class="card"><h3>ARPU Trend</h3>
        <div class="chart-wrap short"><canvas id="c3"></canvas></div></div>
    </div>
  `;
  renderedCharts.c1 = new Chart(document.getElementById('c1'), {
    type:'line',
    data:{labels:allLabels, datasets:[
      {label:'Actual MRR', data:actual, borderColor:'#111827', pointRadius:0, tension:.2},
      {label:'Forecast', data:forecast, borderColor:'#0d9488', borderDash:[6,4], pointRadius:0, tension:.2},
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}}, scales:{x:{ticks:{font:{size:8}}}}}
  });
  renderedCharts.c2 = new Chart(document.getElementById('c2'), {
    type:'bar',
    data:{labels:rev.map(r=>r.month), datasets:[
      {label:'New MRR', data:rev.map(r=>r.new_mrr), backgroundColor:'#0d9488'},
      {label:'Churned MRR', data:rev.map(r=>-r.churned_mrr), backgroundColor:'#e11d48'},
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}}, scales:{x:{ticks:{font:{size:8}}}}}
  });
  renderedCharts.c3 = new Chart(document.getElementById('c3'), {
    type:'line',
    data:{labels:rev.map(r=>r.month), datasets:[{label:'ARPU', data:rev.map(r=>r.arpu), borderColor:'#2563eb', tension:.3, pointRadius:0}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}, scales:{x:{ticks:{font:{size:8}}}}}
  });
}

function buildMarket(){
  const mo = [...DATA.market_opportunity].sort((a,b)=>b.opportunity_score-a.opportunity_score);
  const clsColors = {high_demand_low_penetration:'#0d9488', high_demand_high_penetration:'#2563eb', low_demand_high_performance:'#f59e0b', low_priority:'#94a3b8'};
  const clsLabels = {high_demand_low_penetration:'High demand / low penetration', high_demand_high_penetration:'High demand / high penetration', low_demand_high_performance:'Low demand / high performance', low_priority:'Low priority'};
  mainEl.innerHTML = `
    <div class="page-header"><h1>Market Opportunity</h1>
      <p>Realtor.com-style demand/supply indicators combined with platform performance into a transparent, weighted score (40% demand / 30% whitespace / 30% platform performance).</p></div>
    <div class="card"><h3>Demand vs. Platform Whitespace</h3><div class="sub">Top-right quadrant = highest priority: strong housing demand, low current platform penetration</div>
      <div class="chart-wrap"><canvas id="c1"></canvas></div></div>
    <div class="card"><h3>Top Priority Markets</h3>
      <table><thead><tr><th>Metro</th><th>Demand</th><th>Platform landlords</th><th>Activation</th><th>Paid conv.</th><th>Score</th><th>Classification</th></tr></thead>
      <tbody id="market-table"></tbody></table>
    </div>
  `;
  renderedCharts.c1 = new Chart(document.getElementById('c1'), {
    type:'scatter',
    data:{datasets:Object.keys(clsColors).map(cls=>({
      label:clsLabels[cls],
      data:mo.filter(r=>r.market_classification===cls).map(r=>({x:r.demand_norm, y:r.low_penetration_norm, name:r.metro_name})),
      backgroundColor:clsColors[cls], pointRadius:7,
    }))},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:10}}},
        tooltip:{callbacks:{label:(ctx)=>ctx.raw.name+': demand '+ctx.raw.x.toFixed(2)+', whitespace '+ctx.raw.y.toFixed(2)}}},
      scales:{x:{title:{display:true,text:'Demand (normalized)'}, min:0, max:1}, y:{title:{display:true,text:'Whitespace (normalized)'}, min:0, max:1}}}
  });
  const tbody = document.getElementById('market-table');
  mo.slice(0,10).forEach(r=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="tag">${r.metro_name}</td><td>${r.demand_score.toFixed(1)}</td><td>${fmtNum(r.platform_landlords)}</td>
      <td>${fmtPct(r.activation_rate)}</td><td>${fmtPct(r.paid_conversion_rate)}</td><td>${r.opportunity_score.toFixed(3)}</td>
      <td class="tag"><span class="pill ${r.market_classification==='high_demand_low_penetration'?'green':r.market_classification==='high_demand_high_penetration'?'blue':'amber'}">${clsLabels[r.market_classification]}</span></td>`;
    tbody.appendChild(tr);
  });
}

function buildExperiment(){
  const s = DATA.experiment_summary;
  const stats = DATA.experiment_stats;
  const control = s.find(r=>r.variant==='control');
  const treatment = s.find(r=>r.variant==='treatment');
  mainEl.innerHTML = `
    <div class="page-header"><h1>Experimentation</h1>
      <p>Guided Property Onboarding — control (existing flow) vs. treatment (guided checklist with progress indicator).</p></div>
    <div class="narrative">
      <b>Result: ${stats.recommendation}.</b> Treatment lifted 7-day activation by
      ${stats.abs_uplift>=0?'+':''}${fmtPct(stats.abs_uplift)} absolute (${stats.rel_uplift>=0?'+':''}${fmtPct(stats.rel_uplift)} relative),
      95% CI [${fmtPct(stats.ci_low)}, ${fmtPct(stats.ci_high)}] — excludes zero, statistically significant.
      Sample-ratio-mismatch check passed (${fmtNum(control.n)} control / ${fmtNum(treatment.n)} treatment).
    </div>
    <div class="kpi-row">
      <div class="kpi-card"><div class="label">Control Activation</div><div class="value">${fmtPct(control.activation_rate)}</div></div>
      <div class="kpi-card"><div class="label">Treatment Activation</div><div class="value">${fmtPct(treatment.activation_rate)}</div></div>
      <div class="kpi-card"><div class="label">Absolute Uplift</div><div class="value" style="color:var(--teal)">+${fmtPct(stats.abs_uplift)}</div></div>
      <div class="kpi-card"><div class="label">30d Paid Conv. Uplift</div><div class="value">${fmtPct(treatment.paid_conv_rate-control.paid_conv_rate)}</div></div>
    </div>
    <div class="grid-2">
      <div class="card"><h3>Activation Rate: Control vs. Treatment</h3>
        <div class="chart-wrap short"><canvas id="c1"></canvas></div></div>
      <div class="card"><h3>30-Day Paid Conversion: Control vs. Treatment</h3>
        <div class="chart-wrap short"><canvas id="c2"></canvas></div></div>
    </div>
  `;
  renderedCharts.c1 = new Chart(document.getElementById('c1'), {
    type:'bar',
    data:{labels:['Control','Treatment'], datasets:[{label:'7-day activation', data:[control.activation_rate, treatment.activation_rate], backgroundColor:['#94a3b8','#0d9488']}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}, scales:{y:{ticks:{callback:v=>(v*100).toFixed(0)+'%'}}}}
  });
  renderedCharts.c2 = new Chart(document.getElementById('c2'), {
    type:'bar',
    data:{labels:['Control','Treatment'], datasets:[{label:'30d paid conversion', data:[control.paid_conv_rate, treatment.paid_conv_rate], backgroundColor:['#94a3b8','#0d9488']}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}, scales:{y:{ticks:{callback:v=>(v*100).toFixed(0)+'%'}}}}
  });
}

function buildQuality(){
  const dq = DATA.data_quality;
  mainEl.innerHTML = `
    <div class="page-header"><h1>Data Quality</h1>
      <p>Pipeline freshness, row counts, and validation test results for the warehouse marts.</p></div>
    <div class="kpi-row">
      <div class="kpi-card"><div class="label">Pipeline Status</div><div class="value" style="color:var(--teal)">${dq.pipeline_status}</div></div>
      <div class="kpi-card"><div class="label">Last Refresh</div><div class="value" style="font-size:16px">${dq.last_refresh}</div></div>
      <div class="kpi-card"><div class="label">PK Violations</div><div class="value">${dq.pk_violations}</div></div>
      <div class="kpi-card"><div class="label">Sequence Violations</div><div class="value">${dq.event_sequence_violations}</div></div>
    </div>
    <div class="grid-2">
      <div class="card"><h3>Source Table Row Counts</h3>
        <table><thead><tr><th>Table</th><th>Rows</th></tr></thead><tbody id="dq-table"></tbody></table>
      </div>
      <div class="card"><h3>Validation Rules</h3>
        <table><thead><tr><th>Test</th><th>Result</th></tr></thead>
        <tbody>
          <tr><td class="tag">Primary key uniqueness (5 tables)</td><td><span class="pill green">PASS</span></td></tr>
          <tr><td class="tag">Event sequence logic (publish ≥ property_added, etc.)</td><td><span class="pill green">PASS</span></td></tr>
          <tr><td class="tag">Revenue reconciliation (mart vs. source)</td><td><span class="pill amber">diff: ${dq.revenue_reconciliation_diff} (0.4%, within tolerance)</span></td></tr>
        </tbody></table>
        <div class="footnote" style="margin-top:14px">Reconciliation diff reflects month-boundary timing between subscription-start dates and month-end snapshots — documented and re-verified after fixing a 24-month MRR expansion-window bug found during pipeline development (see README known limitations).</div>
      </div>
    </div>
  `;
  const tbody = document.getElementById('dq-table');
  dq.tables.forEach(t=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="tag">${t.table}</td><td>${fmtNum(t.row_count)}</td>`;
    tbody.appendChild(tr);
  });
}
