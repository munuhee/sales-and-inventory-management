// Point of sale. Prices are always recalculated on the server.
(function () {
  'use strict';

  var currency = JSON.parse(document.getElementById('currency').textContent);
  var loyaltyCfg = JSON.parse(document.getElementById('loyalty-config').textContent);
  var csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
  var $ = window.jQuery;

  // Money is handled in integer cents so floating point rounding never shows.
  function toCents(value) {
    var n = Number(value);
    return isFinite(n) ? Math.round(n * 100) : 0;
  }
  function fmt(cents) {
    var s = (Math.abs(cents) / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return (cents < 0 ? '-' : '') + currency + ' ' + s;
  }
  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { node.setAttribute(k, attrs[k]); });
    if (text !== undefined) node.textContent = text;
    return node;
  }

  var cart = [];        // {id, name, priceCents, stock, qty}
  var customer = null;  // {id, text, loyalty_points}

  var body = document.getElementById('cart-body');
  var emptyState = document.getElementById('cart-empty');
  var errorBox = document.getElementById('form-error');
  var clearButton = document.getElementById('clear-cart');
  var cartCount = document.getElementById('cart-count');

  function renderCart() {
    body.textContent = '';
    cart.forEach(function (line, index) {
      var tr = el('tr');
      var name = el('td');
      name.appendChild(el('div', { 'class': 'fw-medium' }, line.name));
      name.appendChild(el('div', { 'class': 'small text-muted' }, line.stock + ' in stock'));
      tr.appendChild(name);
      tr.appendChild(el('td', { 'class': 'num' }, fmt(line.priceCents)));

      var amount = el('td', { 'class': 'num' }, fmt(line.priceCents * line.qty));
      var qtyCell = el('td', { 'class': 'num' });
      var qty = el('input', {
        type: 'number', min: '1', max: String(line.stock), step: '1',
        value: String(line.qty), 'class': 'form-control form-control-sm qty-input ms-auto',
        'aria-label': 'Quantity of ' + line.name
      });
      qty.addEventListener('input', function () {
        var v = parseInt(qty.value, 10);
        if (!isFinite(v) || v < 1) v = 1;
        if (v > line.stock) v = line.stock;
        line.qty = v;
        amount.textContent = fmt(line.priceCents * line.qty);
        recalc();
      });
      qty.addEventListener('blur', function () { qty.value = String(line.qty); });
      qtyCell.appendChild(qty);
      tr.appendChild(qtyCell);
      tr.appendChild(amount);

      var actions = el('td', { 'class': 'row-actions' });
      var remove = el('button', { type: 'button', 'class': 'danger', title: 'Remove', 'aria-label': 'Remove ' + line.name });
      remove.appendChild(el('i', { 'class': 'fa-solid fa-xmark' }));
      remove.addEventListener('click', function () { cart.splice(index, 1); renderCart(); });
      actions.appendChild(remove);
      tr.appendChild(actions);
      body.appendChild(tr);
    });
    emptyState.hidden = cart.length > 0;
    document.getElementById('cart-table').hidden = cart.length === 0;
    cartCount.textContent = cart.length + ' item' + (cart.length === 1 ? '' : 's');
    clearButton.disabled = cart.length === 0;
    recalc();
  }

  function maxRedeem(subCents) {
    if (!customer || !loyaltyCfg.enabled) return 0;
    var pointCents = toCents(loyaltyCfg.point_value);
    if (pointCents <= 0) return 0;
    return Math.max(0, Math.min(customer.loyalty_points, Math.floor(subCents / pointCents)));
  }

  function totals() {
    var sub = cart.reduce(function (sum, l) { return sum + l.priceCents * l.qty; }, 0);
    var redeemInput = document.getElementById('redeem');
    var redeem = redeemInput ? Math.max(0, parseInt(redeemInput.value, 10) || 0) : 0;
    redeem = Math.min(redeem, maxRedeem(sub));
    var discount = redeem * toCents(loyaltyCfg.point_value || 0);
    var taxRate = Math.min(100, Math.max(0, Number(document.getElementById('tax').value) || 0));
    var taxable = sub - discount;
    var tax = Math.round(taxable * taxRate / 100);
    var total = taxable + tax;
    var paidRaw = document.getElementById('paid').value;
    var paid = paidRaw === '' ? null : toCents(paidRaw);
    return { sub: sub, redeem: redeem, discount: discount, tax: tax, total: total, paid: paid, taxRate: taxRate };
  }

  function recalc() {
    var t = totals();
    document.getElementById('t-sub').textContent = fmt(t.sub);
    document.getElementById('t-discount').textContent = '-' + fmt(t.discount);
    document.getElementById('row-discount').hidden = t.discount === 0;
    document.getElementById('t-tax').textContent = fmt(t.tax);
    document.getElementById('t-total').textContent = fmt(t.total);
    var changeEl = document.getElementById('t-change');
    if (t.paid === null) {
      changeEl.textContent = fmt(0);
    } else {
      changeEl.textContent = t.paid >= t.total ? fmt(t.paid - t.total) : 'Short by ' + fmt(t.total - t.paid);
    }
    var box = document.getElementById('loyalty-box');
    if (box) {
      box.hidden = !customer || customer.loyalty_points <= 0;
      if (customer) {
        document.getElementById('redeem').max = String(maxRedeem(t.sub));
        document.getElementById('loyalty-hint').textContent =
          customer.loyalty_points + ' points available, worth ' +
          fmt(customer.loyalty_points * toCents(loyaltyCfg.point_value)) + '.';
      }
    }
  }

  function showError(message) {
    errorBox.textContent = message || '';
    errorBox.hidden = !message;
  }

  $('#customer').select2({
    width: '100%',
    dropdownParent: $('#customer').closest('.pos-checkout'),
    placeholder: 'Search by name or phone',
    allowClear: true,
    language: { noResults: function () { return 'No customers match. Try another name or phone.'; } },
    ajax: {
      url: document.getElementById('customer').dataset.url,
      dataType: 'json',
      delay: 200,
      data: function (params) { return { term: params.term || '' }; },
      processResults: function (data) { return data; }
    },
    templateResult: function (c) {
      if (!c.id) return c.text;
      var wrap = el('div', { 'class': 'select2-option' });
      wrap.appendChild(el('div', {}, c.text));
      wrap.appendChild(el('div', { 'class': 'stock' }, [c.phone, (c.loyalty_points || 0) + ' pts'].filter(Boolean).join(' · ')));
      return $(wrap);
    }
  }).on('select2:select', function (e) {
    customer = { id: e.params.data.id, text: e.params.data.text, loyalty_points: e.params.data.loyalty_points || 0 };
    var r = document.getElementById('redeem'); if (r) r.value = 0;
    recalc();
  }).on('select2:clear', function () { customer = null; recalc(); });

  $('#item-search').select2({
    width: '100%',
    dropdownParent: $('#item-search').closest('.pos-picker'),
    placeholder: 'Type a product name',
    minimumInputLength: 1,
    language: {
      inputTooShort: function () { return 'Type at least one character to search.'; },
      noResults: function () { return 'No in-stock products match. Refine your search or add stock.'; }
    },
    ajax: {
      url: document.getElementById('item-search').dataset.url,
      dataType: 'json',
      delay: 200,
      data: function (params) { return { term: params.term || '' }; },
      processResults: function (data) { return { results: data }; }
    },
    templateResult: function (item) {
      if (!item.id) return item.text;
      var wrap = el('div', { 'class': 'select2-option d-flex justify-content-between gap-3' });
      wrap.appendChild(el('span', {}, item.name));
      wrap.appendChild(el('span', { 'class': 'stock' }, fmt(toCents(item.price)) + ' · ' + item.stock + ' in stock'));
      return $(wrap);
    }
  }).on('select2:select', function (e) {
    var item = e.params.data;
    var existing = cart.find(function (l) { return String(l.id) === String(item.id); });
    if (existing) {
      existing.qty = Math.min(existing.stock, existing.qty + 1);
    } else {
      cart.push({ id: item.id, name: item.name, priceCents: toCents(item.price), stock: item.stock, qty: 1 });
    }
    $(this).val(null).trigger('change');
    renderCart();
  });

  ['tax', 'paid', 'redeem'].forEach(function (id) {
    var node = document.getElementById(id);
    if (node) node.addEventListener('input', recalc);
  });
  var redeemMax = document.getElementById('redeem-max');
  if (redeemMax) redeemMax.addEventListener('click', function () {
    document.getElementById('redeem').value = maxRedeem(totals().sub);
    recalc();
  });
  document.getElementById('paid-exact').addEventListener('click', function () {
    document.getElementById('paid').value = (totals().total / 100).toFixed(2);
    recalc();
  });
  document.getElementById('clear-cart').addEventListener('click', function () {
    if (cart.length && window.confirm('Remove all items from this sale?')) { cart = []; renderCart(); }
  });

  function resetSale() {
    cart = [];
    customer = null;
    $('#customer').val(null).trigger('change');
    document.getElementById('tax').value = 0;
    document.getElementById('paid').value = '';
    var r = document.getElementById('redeem'); if (r) r.value = 0;
    showError('');
    renderCart();
  }

  var modal = new bootstrap.Modal(document.getElementById('done-modal'));
  document.getElementById('done-new').addEventListener('click', function () { modal.hide(); resetSale(); });

  document.addEventListener('keydown', function (event) {
    var target = event.target;
    var isTyping = target && (target.isContentEditable || /INPUT|TEXTAREA|SELECT/.test(target.tagName));
    if (event.key === '/' && !isTyping && !event.altKey && !event.ctrlKey && !event.metaKey) {
      event.preventDefault();
      $('#item-search').select2('open');
    }
  });

  document.getElementById('sale-form').addEventListener('submit', function (event) {
    event.preventDefault();
    showError('');
    var t = totals();
    if (!customer) {
      showError('Select a customer to continue.');
      $('#customer').select2('open');
      return;
    }
    if (!cart.length) {
      showError('Add at least one product to the cart.');
      $('#item-search').select2('open');
      return;
    }
    if (t.paid === null || t.paid < t.total) {
      showError('Amount paid must cover the sale total.');
      document.getElementById('paid').focus();
      return;
    }

    var button = document.getElementById('submit-btn');
    button.disabled = true;
    button.textContent = 'Saving...';

    fetch(window.location.pathname, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify({
        customer: customer.id,
        items: cart.map(function (l) { return { id: l.id, quantity: l.qty }; }),
        tax_percentage: t.taxRate,
        amount_paid: (t.paid / 100).toFixed(2),
        redeem_points: t.redeem
      })
    }).then(function (response) {
      return response.json().catch(function () { return { status: 'error', message: 'Unexpected server response.' }; });
    }).then(function (data) {
      if (data.status !== 'success') { showError(data.message || 'The sale could not be saved.'); return; }
      document.getElementById('done-receipt').textContent = data.receipt_number;
      document.getElementById('done-total').textContent = fmt(toCents(data.grand_total));
      document.getElementById('done-change').textContent = fmt(toCents(data.change));
      var points = document.getElementById('done-points');
      points.textContent = data.points_earned ? data.points_earned + ' loyalty points earned' : '';
      points.hidden = !data.points_earned;
      document.getElementById('done-print').href = data.receipt_url;
      document.getElementById('done-view').href = data.redirect;
      modal.show();
    }).catch(function () {
      showError('Network error. Check the connection and try again.');
    }).finally(function () {
      button.disabled = false;
      button.textContent = 'Complete sale';
    });
  });

  renderCart();
})();
