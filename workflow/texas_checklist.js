// Texas resale file pre-review. Runs as the "Texas checklist" Function block in Sim.
// Input: <start.file>, a transaction file as structured data (cover sheet, tax record, documents).
// Output: { decision: "clear" | "hold" | "escalate", issues: [{code, severity, detail}], summary }
// "clear" means ready for the Texas broker review stage. It never approves a commission payout.
const file = <start.file>;
const off = new Set((file.test_options && file.test_options.disabled_checks) || []); // ablation test only

const cs = file.cover_sheet;
const tax = file.tax_record || {};
const docs = file.documents || [];
const issues = [];
const add = (code, severity, detail) => issues.push({ code, severity, detail });

const norm = (s) => String(s || '').toLowerCase().replace(/[^a-z0-9]/g, '');
const sameAddress = (a, b) => norm(a) === norm(b);
const days = (a, b) => Math.round((new Date(b) - new Date(a)) / 86400000);

// 1. Documents filed under another property (Side's "document from another transaction")
const ownDocs = [];
for (const d of docs) {
  if (!off.has('wrong_file') && d.address && !sameAddress(d.address, cs.address)) {
    add('WRONG_TRANSACTION_DOC', 'hold', `${d.type} is for ${d.address}, not ${cs.address}`);
  } else {
    ownDocs.push(d);
  }
}
const find = (type) => ownDocs.find((d) => d.type === type);
const has = (type) => Boolean(find(type));

// 2. Property facts must match the county tax record
if (!file.tax_record) {
  add('MISSING_TAX_RECORD', 'hold', 'no tax record in file'); // a common return reason in Side's guide
} else if (!off.has('tax_match')) {
  if (!sameAddress(cs.address, tax.address)) {
    add('PROPERTY_MISMATCH', 'hold', `cover sheet address ${cs.address} vs tax record ${tax.address}`);
  }
  if (cs.year_built && tax.year_built && Number(cs.year_built) !== Number(tax.year_built)) {
    add('YEAR_BUILT_MISMATCH', 'hold', `cover sheet says ${cs.year_built}, tax record says ${tax.year_built}`);
  }
  const sellerIsOwner = (cs.sellers || []).some((s) => norm(s) === norm(tax.owner));
  const ownerExplained = cs.seller_type === 'estate' ? has('Letters Testamentary') : cs.seller_type === 'entity' ? has('Entity Authority') : false;
  if (!sellerIsOwner && !ownerExplained) {
    add('SELLER_NOT_OWNER', 'escalate', `seller ${(cs.sellers || []).join(', ')} does not match owner of record ${tax.owner}`);
  }
}

// 3. Required documents for every Texas sale file
if (!off.has('iabs') && !has('IABS')) {
  add('MISSING_IABS', 'hold', 'Information About Brokerage Services notice (TREC IABS 1-2) not in file');
}
const contract = find('Resale Contract');
if (!contract) {
  add('MISSING_CONTRACT', 'hold', 'One to Four Family Residential Contract (TREC 20-18) not in file');
} else if (!off.has('signatures')) {
  const needed = [...(cs.buyers || []), ...(cs.sellers || [])];
  const missing = needed.filter((p) => !(contract.signed_by || []).map(norm).includes(norm(p)));
  if (missing.length) add('CONTRACT_NOT_EXECUTED', 'hold', `contract missing signature(s): ${missing.join(', ')}`);
}

// 4. Conditional addenda (TREC 20-18 paragraph 22)
if (!off.has('financing') && cs.financing !== 'cash' && !has('Third Party Financing Addendum')) {
  add('MISSING_TPF_ADDENDUM', 'hold', `${cs.financing} financing but no Third Party Financing Addendum`);
}
if (!off.has('hoa') && cs.hoa && !has('HOA Addendum')) {
  add('MISSING_HOA_ADDENDUM', 'hold', 'property is in a mandatory owners association but no HOA addendum');
}
const builtYear = Number(tax.year_built || cs.year_built); // tax record wins
if (!off.has('lead_paint') && builtYear && builtYear < 1978) {
  const lbp = find('Lead-Based Paint Addendum');
  if (!lbp) {
    add('MISSING_LBP_ADDENDUM', 'hold', `built ${builtYear}, before 1978, but no lead-based paint addendum`);
  } else if (contract && lbp.date && contract.date && new Date(lbp.date) > new Date(contract.date)) {
    add('LBP_AFTER_CONTRACT', 'escalate', `lead-based paint addendum dated ${lbp.date}, after the contract (${contract.date})`);
  }
}

// 5. Seller's Disclosure Notice (Tex. Prop. Code 5.008), with the exemptions a file can show
const sdnExempt = ['estate', 'foreclosure', 'government', 'new_construction'].includes(cs.seller_type);
if (!off.has('seller_disclosure') && !sdnExempt && !has("Seller's Disclosure Notice")) {
  add('MISSING_SELLER_DISCLOSURE', 'hold', "Seller's Disclosure Notice not in file and no exemption shown");
}

// 6. Entity sellers need proof of signing authority
if (!off.has('authority') && cs.seller_type === 'entity' && !has('Entity Authority')) {
  add('MISSING_ENTITY_AUTHORITY', 'hold', 'entity seller but no articles or resolution showing who can sign');
}

// 7. Earnest money: within 3 days after the Effective Date (TREC 20-18 paragraph 5)
if (!off.has('earnest_money') && cs.status !== 'terminated') {
  const em = find('Earnest Money Receipt');
  if (!em) {
    add('MISSING_EM_RECEIPT', 'hold', 'no earnest money receipt from the escrow agent');
  } else if (cs.effective_date && days(cs.effective_date, em.date) > 3) {
    add('EM_LATE', 'escalate', `earnest money receipted ${em.date}, ${days(cs.effective_date, em.date)} days after the ${cs.effective_date} Effective Date`);
  }
}

// 8. Terminated files need a signed release of earnest money
if (!off.has('termination') && cs.status === 'terminated' && !has('Release of Earnest Money')) {
  add('MISSING_EM_RELEASE', 'hold', 'file is terminated but there is no Release of Earnest Money');
}

// 9. Closed files: final closing statement must match the cover sheet
if (!off.has('closing') && cs.status === 'closed') {
  const st = find('Closing Statement');
  if (!st) {
    add('MISSING_CLOSING_STATEMENT', 'hold', 'closed file but no final closing statement');
  } else {
    if (Number(st.price) !== Number(cs.price)) add('CLOSING_PRICE_MISMATCH', 'escalate', `closing statement price ${st.price} vs cover sheet ${cs.price}`);
    if (st.close_date !== cs.close_date) add('CLOSING_DATE_MISMATCH', 'escalate', `closing statement date ${st.close_date} vs cover sheet ${cs.close_date}`);
  }
}

const decision = issues.some((i) => i.severity === 'escalate') ? 'escalate' : issues.length ? 'hold' : 'clear';
const summary = decision === 'clear'
  ? `${cs.address}: no issues found, ready for broker review`
  : `${cs.address}: ${issues.length} issue(s), ${decision}`;
return { file_id: file.file_id, decision, issues, summary };
