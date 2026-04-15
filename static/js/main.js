/**
    * selectImages
    * menuleft
    * tabs
    * progresslevel
    * collapse_menu
    * fullcheckbox
    * showpass
    * gallery
    * coppy
    * select_colors_theme
    * icon_function
    * box_search
    * preloader
*/

; (function ($) {

  "use strict";

  var selectImages = function () {
    if ($(".image-select").length > 0) {
      const selectIMG = $(".image-select");
      selectIMG.find("option").each((idx, elem) => {
        const selectOption = $(elem);
        const imgURL = selectOption.attr("data-thumbnail");
        if (imgURL) {
          selectOption.attr(
            "data-content",
            "<img src='%i'/> %s"
              .replace(/%i/, imgURL)
              .replace(/%s/, selectOption.text())
          );
        }
      });
      selectIMG.selectpicker();
    }
  };

  var menuleft = function () {
    if ($('div').hasClass('section-menu-left')) {
      var bt =$(".section-menu-left").find(".has-children");
      bt.on("click", function () {
        var args = { duration: 200 };
        if ($(this).hasClass("active")) {
          $(this).children(".sub-menu").slideUp(args);
          $(this).removeClass("active");
        } else {
          $(".sub-menu").slideUp(args);
          $(this).children(".sub-menu").slideDown(args);
          $(".menu-item.has-children").removeClass("active");
          $(this).addClass("active");
        }
      });
      $('.sub-menu-item').on('click', function(event){
        event.stopPropagation();
      });
    }
  };

  var tabs = function(){
    $('.widget-tabs').each(function(){
        $(this).find('.widget-content-tab').children().hide();
        $(this).find('.widget-content-tab').children(".active").show();
        $(this).find('.widget-menu-tab').find('li').on('click',function(){
            var liActive = $(this).index();
            var contentActive=$(this).siblings().removeClass('active').parents('.widget-tabs').find('.widget-content-tab').children().eq(liActive);
            contentActive.addClass('active').fadeIn("slow");
            contentActive.siblings().removeClass('active');
            $(this).addClass('active').parents('.widget-tabs').find('.widget-content-tab').children().eq(liActive).siblings().hide();
        });
    });
  };

  $('ul.dropdown-menu.has-content').on('click', function(event){
    event.stopPropagation();
  });
  $('.button-close-dropdown').on('click', function(){
    $(this).closest('.dropdown').find('.dropdown-toggle').removeClass('show');
    $(this).closest('.dropdown').find('.dropdown-menu').removeClass('show');
  });

  var progresslevel = function () {
    if ($('div').hasClass('progress-level-bar')) {
    var bars = document.querySelectorAll('.progress-level-bar > span');
    setInterval(function(){
    bars.forEach(function(bar){
      var t1 = parseFloat(bar.dataset.progress);
      var t2 = parseFloat(bar.dataset.max);
      var getWidth = ( t1 / t2) * 100;
      bar.style.width = getWidth + '%';
    });
    }, 500);
  }}

  var collapse_menu = function () {
    $(".button-show-hide").on("click", function () {
      $('.layout-wrap').toggleClass('full-width');
    })
  }

  var fullcheckbox = function () {
    $('.total-checkbox').on('click', function () {
      if ( $(this).is(':checked') ) {
        $(this).closest('.wrap-checkbox').find('.checkbox-item').prop('checked', true);
      } else {
        $(this).closest('.wrap-checkbox').find('.checkbox-item').prop('checked', false);
      }
    });
  };

  var showpass = function() {
    $(".show-pass").on("click", function () {
      $(this).toggleClass("active");
      var input = $(this).parents(".password").find(".password-input");

      if (input.attr("type") === "password") {
        input.attr("type", "text");
      } else if (input.attr("type") === "text") {
        input.attr("type", "password");
      }
    });
  }

  var gallery = function() {
    $(".button-list-style").on("click", function () {
      $(".wrap-gallery-item").addClass("list");
    });
    $(".button-grid-style").on("click", function () {
      $(".wrap-gallery-item").removeClass("list");
    });
  }

  var coppy = function() {
    $(".button-coppy").on("click", function () {
      myFunction()
    });
    function myFunction() {
      var copyText = document.getElementsByClassName("coppy-content");
      navigator.clipboard.writeText(copyText.text);
    }
  }

  var select_colors_theme = function () {
    if ($('div').hasClass("select-colors-theme")) {
      $(".select-colors-theme .item").on("click", function (e) {
        $(this).parents(".select-colors-theme").find(".active").removeClass("active");
        $(this).toggleClass("active");
      })
    }
  }

  var icon_function = function () {
    if ($('div').hasClass("list-icon-function")) {
      $(".list-icon-function .trash").on("click", function (e) {
        $(this).parents(".product-item").remove();
        $(this).parents(".attribute-item").remove();
        $(this).parents(".countries-item").remove();
        $(this).parents(".user-item").remove();
        $(this).parents(".roles-item").remove();
      })
    }
  }

  var box_search=function(){
        
    $(document).on('click',function(e){
      var clickID=e.target.id;if((clickID!=='s')){
          $('.box-content-search').removeClass('active');
      }});
    $(document).on('click',function(e){
        var clickID=e.target.class;if((clickID!=='a111')){
            $('.show-search').removeClass('active');
    }});
        
    $('.show-search').on('click',function(event){
      event.stopPropagation();}
    );
    $('.search-form').on('click',function(event){
      event.stopPropagation();}
    );
    var input =  $('.header-dashboard').find('.form-search').find('input');
    input.on('input', function() {
      if ($(this).val().trim() !== '') {
        $('.box-content-search').addClass('active');
      } else {
        $('.box-content-search').removeClass('active');
      }
    });
   
  }

  var retinaLogos = function() {
    var retina = window.devicePixelRatio > 1 ? true : false;
      if(retina) {
        if ($(".dark-theme").length > 0) {
          $('#logo_header').attr({src:'images/logo/logo.png',width:'154px',height:'52px'});
        } else {
          $('#logo_header').attr({src:'images/logo/logo.png',width:'154px',height:'52px'});
        }
      }
  };  

  var preloader = function () {
    setTimeout(function () {
    $("#preload").fadeOut("slow", function () {
        $(this).remove();
    });
    }, 1000);
  };


  // Dom Ready
  $(function () {
    selectImages();
    menuleft();
    tabs();
    progresslevel();
    collapse_menu();
    fullcheckbox();
    showpass();
    gallery();
    coppy();
    select_colors_theme();
    icon_function();
    box_search();
    retinaLogos();
    preloader();
    
  });

})(jQuery);

    // Single image preview
    document.getElementById('myFile').addEventListener('change', function (e) {
        const file = e.target.files[0];
        if (file) {
            const preview = document.getElementById('imgpreview');
            const img = document.getElementById('previewImg');
            img.src = URL.createObjectURL(file);
            preview.style.display = 'block';
        }
    });

    // Remove single image preview
    function removeSingleImage() {
        document.getElementById('previewImg').src = '';
        document.getElementById('imgpreview').style.display = 'none';
        document.getElementById('myFile').value = '';
    }

    // Multiple gallery image preview
    document.getElementById('gFile').addEventListener('change', function (e) {
    const files = e.target.files;
    const gallery = document.getElementById('galleryPreview');

    // Remove old previews (keep upload button only)
    gallery.querySelectorAll('.preview-thumb').forEach(el => el.remove());

    for (let i = 0; i < files.length; i++) {
        const imgUrl = URL.createObjectURL(files[i]);
        const wrapper = document.createElement('div');
        wrapper.classList.add('item', 'preview-thumb');

        wrapper.innerHTML = `
            <img src="${imgUrl}" alt="">
            <button type="button" class="remove-btn">×</button>
        `;

        // Insert before upload button
        gallery.insertBefore(wrapper, document.getElementById('galUpload'));

        // Remove image on click
        wrapper.querySelector('.remove-btn').addEventListener('click', () => {
            wrapper.remove();
        });
    }

    // ❌ Do NOT reset input here
    // e.target.value = '';
});



/**
 * variants.js
 * Product Variant Manager — Django E-commerce Admin
 * Handles: toggle, add/remove options, cartesian variant generation,
 * data preservation on re-render, edit-mode auto-init, image preview
 */

'use strict';

// ─── State ───────────────────────────────────────────────────────────────────
let optionIndex = 0; // unique counter for new option rows (never reused)

// ─── DOM Ready ───────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    initToggle();
    initFromExistingProduct();
});

// ─── Toggle Logic ────────────────────────────────────────────────────────────
function initToggle() {
    const toggle = document.getElementById('productTypeToggleSwitch');
    if (!toggle) return;

    toggle.addEventListener('change', function () {
        const input = document.getElementById('productTypeInput');
        const section = document.getElementById('variantSection');
        const badge = document.getElementById('productTypeBadge');

        if (this.checked) {
            input.value = 'variable';
            section.style.display = 'block';
            if (badge) { badge.textContent = 'Variable'; badge.className = 'type-badge variable'; }
            generateVariants();
        } else {
            input.value = 'simple';
            section.style.display = 'none';
            if (badge) { badge.textContent = 'Simple'; badge.className = 'type-badge simple'; }
        }
    });
}

// ─── Edit Mode: Auto-init on page load ───────────────────────────────────────
/**
 * If product_type hidden input is "variable" (set by Django template),
 * automatically turn the toggle ON and set up all listeners.
 * This fixes the bug where edit page required manual toggle off/on.
 */
function initFromExistingProduct() {
    const input = document.getElementById('productTypeInput');
    const toggle = document.getElementById('productTypeToggleSwitch');
    const section = document.getElementById('variantSection');
    const badge = document.getElementById('productTypeBadge');

    if (!input || !toggle || !section) return;

    if (input.value === 'variable') {
        // Force toggle ON without firing the 'change' event
        toggle.checked = true;
        section.style.display = 'block';
        if (badge) { badge.textContent = 'Variable'; badge.className = 'type-badge variable'; }

        // Attach listeners to existing option rows (rendered by Django template)
        document.querySelectorAll('#optionContainer .option-row-wrap').forEach(function (wrap) {
            attachOptionListeners(wrap);
        });

        // Set optionIndex so new options don't clash with existing indices
        const existing = document.querySelectorAll('#optionContainer .option-row-wrap');
        optionIndex = existing.length;

        // Generate variants from pre-filled option inputs
        generateVariants();
    }
}

// ─── Add Option Row ───────────────────────────────────────────────────────────
function addOption() {
    const container = document.getElementById('optionContainer');
    const emptyMsg = document.getElementById('noOptionsMsg');

    const wrap = document.createElement('div');
    wrap.className = 'option-row-wrap';
    wrap.dataset.idx = optionIndex;

    wrap.innerHTML = `
        <div class="opt-row">
            <div class="opt-field">
                <label>Option Name</label>
                <input type="text"
                    class="form-control option-name"
                    name="options[${optionIndex}][name]"
                    placeholder="e.g. Size, Color, Material">
            </div>
            <div class="opt-field">
                <label>Values <small>(comma separated)</small></label>
                <input type="text"
                    class="form-control option-values"
                    name="options[${optionIndex}][value]"
                    placeholder="e.g. S, M, L  or  Red, Blue, Green">
            </div>
            <button type="button" class="btn-remove-opt" title="Remove option"
                onclick="removeOption(this)">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14"
                    viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"></path>
                    <path d="M10 11v6M14 11v6"></path>
                    <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"></path>
                </svg>
            </button>
        </div>`;

    container.appendChild(wrap);
    attachOptionListeners(wrap);

    if (emptyMsg) emptyMsg.style.display = 'none';
    optionIndex++;
    generateVariants();
}

function removeOption(btn) {
    const wrap = btn.closest('.option-row-wrap');
    if (wrap) {
        wrap.remove();
        updateNoOptionsMsg();
        generateVariants();
    }
}

function attachOptionListeners(wrap) {
    wrap.querySelectorAll('input').forEach(function (el) {
        el.addEventListener('input', generateVariants);
    });
}

function updateNoOptionsMsg() {
    const emptyMsg = document.getElementById('noOptionsMsg');
    const rows = document.querySelectorAll('#optionContainer .option-row-wrap');
    if (emptyMsg) emptyMsg.style.display = rows.length === 0 ? 'block' : 'none';
}

// ─── Cartesian Product ────────────────────────────────────────────────────────
function cartesian(arrays) {
    return arrays.reduce(function (acc, curr) {
        return acc.flatMap(function (a) {
            return curr.map(function (b) {
                return a.concat([b]);
            });
        });
    }, [[]]);
}

// ─── Generate Variants ────────────────────────────────────────────────────────
/**
 * Core function:
 * 1. Reads all option names + values
 * 2. Saves existing variant field data (preserves user input on re-render)
 * 3. Builds cartesian product of all option values
 * 4. Renders variant cards, restoring saved data
 */
function generateVariants() {
    const nameInputs  = Array.from(document.querySelectorAll('#optionContainer .option-name'));
    const valueInputs = Array.from(document.querySelectorAll('#optionContainer .option-values'));

    const variantList  = document.getElementById('variantList');
    const emptyState   = document.getElementById('emptyVariants');
    const countBadge   = document.getElementById('variantCount');
    const collapseBtn  = document.getElementById('collapseAllBtn');

    if (!variantList) return;

    // Build valid pairs (name + at least one value)
    const pairs = [];
    nameInputs.forEach(function (nameEl, i) {
        const name   = nameEl.value.trim();
        const values = valueInputs[i]
            ? valueInputs[i].value.split(',').map(function (v) { return v.trim(); }).filter(Boolean)
            : [];
        if (name && values.length) {
            pairs.push({ name: name, values: values });
        }
    });

    // ── STEP 1: Snapshot existing user-entered data ──────────────────────────
    const saved = {};
    variantList.querySelectorAll('.variant-card').forEach(function (card) {
        const keyEl = card.querySelector('[data-variant-key]');
        if (!keyEl) return;
        const key = keyEl.dataset.variantKey;

        saved[key] = {
            sku:           card.querySelector('[data-f="sku"]')?.value          || '',
            stock:         card.querySelector('[data-f="stock"]')?.value        || '',
            cost_price:    card.querySelector('[data-f="cost_price"]')?.value   || '',
            regular_price: card.querySelector('[data-f="regular_price"]')?.value|| '',
            sale_price:    card.querySelector('[data-f="sale_price"]')?.value   || '',
            points:        card.querySelector('[data-f="points"]')?.value       || '',
            description:   card.querySelector('[data-f="description"]')?.value  || '',
           image_url:
                  card.querySelector('.img-thumb')?.getAttribute('src') ||
                  card.querySelector('input[name*="[old_image]"]')?.value ||
                  '',
            expanded:      card.classList.contains('is-open'),
        };
    });

    // ── STEP 2: Clear list ────────────────────────────────────────────────────
    variantList.innerHTML = '';

    if (!pairs.length) {
        if (emptyState)  emptyState.style.display  = 'flex';
        if (countBadge)  countBadge.textContent     = '0';
        if (collapseBtn) collapseBtn.style.display  = 'none';
        return;
    }

    // ── STEP 3: Build combos ─────────────────────────────────────────────────
    const combos    = cartesian(pairs.map(function (p) { return p.values; }));
    const pairNames = pairs.map(function (p) { return p.name; });

    if (emptyState)  emptyState.style.display  = 'none';
    if (countBadge)  countBadge.textContent     = combos.length;
    if (collapseBtn) collapseBtn.style.display  = 'inline-flex';

    // ── STEP 4: Render each variant card ─────────────────────────────────────
    combos.forEach(function (combo, index) {
        const key        = combo.join(' / ');
        const prev       = saved[key] || {};
        const isOpen     = prev.expanded !== false; // default open for new cards
        const optionsObj = {};
        pairNames.forEach(function (n, i) { optionsObj[n] = combo[i]; });
        const optionsJSON = JSON.stringify(optionsObj).replace(/"/g, '&quot;');

        const tags = combo.map(function (v) {
            return '<span class="vtag">' + escHtml(v) + '</span>';
        }).join('');

        const card = document.createElement('div');
        card.className = 'variant-card' + (isOpen ? ' is-open' : '');

        card.innerHTML = `
            <div class="vc-header" onclick="toggleVariantCard(this)">
                <div class="vc-label" data-variant-key="${escAttr(key)}">
                    <span class="vc-dot"></span>
                    ${tags}
                </div>
                <span class="vc-chevron">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14"
                        viewBox="0 0 24 24" fill="none" stroke="currentColor"
                        stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </span>
            </div>

            <div class="vc-body" style="display:${isOpen ? 'block' : 'none'}">
                <input type="hidden"
                    name="variants[${index}][options]"
                    value="${optionsJSON}">

                <div class="vf-grid">
                    <div class="vf-col">
                        <div class="vf-group">
                            <label>SKU</label>
                            <input type="text"
                                name="variants[${index}][sku]"
                                data-f="sku"
                                placeholder="SKU-001"
                                value="${escAttr(prev.sku)}">
                        </div>
                    </div>
                    <div class="vf-col">
                        <div class="vf-group">
                            <label>Quantity / Stock</label>
                            <input type="number"
                                name="variants[${index}][stock]"
                                data-f="stock"
                                placeholder="0"
                                min="0"
                                value="${escAttr(prev.stock)}">
                        </div>
                    </div>
                    <div class="vf-col full">
                        <div class="vf-group">
                            <label>Cost Price</label>
                            <input type="text"
                                name="variants[${index}][cost_price]"
                                data-f="cost_price"
                                placeholder="0.00"
                                value="${escAttr(prev.cost_price)}">
                        </div>
                    </div>
                    <div class="vf-col">
                        <div class="vf-group">
                            <label>Regular Price <span class="req">*</span></label>
                            <input type="text"
                                name="variants[${index}][regular_price]"
                                data-f="regular_price"
                                placeholder="0.00"
                                required
                                value="${escAttr(prev.regular_price)}">
                        </div>
                    </div>
                    <div class="vf-col">
                        <div class="vf-group">
                            <label>Sale Price</label>
                            <input type="text"
                                name="variants[${index}][sale_price]"
                                data-f="sale_price"
                                placeholder="0.00"
                                value="${escAttr(prev.sale_price)}">
                        </div>
                    </div>
                    <div class="vf-col full">
                        <div class="vf-group">
                            <label>Reward Points</label>
                            <input type="number"
                                name="variants[${index}][points]"
                                data-f="points"
                                placeholder="0"
                                min="0"
                                value="${escAttr(prev.points)}">
                        </div>
                    </div>
                    <div class="vf-col full">
                        <div class="vf-group">
                            <label>Description</label>
                            <textarea
                                name="variants[${index}][description]"
                                data-f="description"
                                placeholder="Optional variant description..."
                                rows="3">${escHtml(prev.description)}</textarea>
                        </div>
                    </div>
                    <div class="vf-col full">
                        <div class="vf-group">
                            <label>Image</label>
                            <input type="file"
                                name="variants[${index}][image]"
                                accept="image/*"
                                onchange="previewImage(this)">
                            ${prev.image_url
                                ? `<div class="img-preview-wrap">
                                       <img src="${escAttr(prev.image_url)}" class="img-thumb" alt="variant image">
                                       <input type="hidden"
                                           name="variants[${index}][old_image]"
                                           value="${escAttr(prev.image_url)}">
                                   </div>`
                                : '<div class="img-preview-wrap" style="display:none"></div>'}
                        </div>
                    </div>
                </div>
            </div>`;

        variantList.appendChild(card);
    });
}

// ─── Collapse / Expand ────────────────────────────────────────────────────────
function toggleVariantCard(header) {
    const card = header.closest('.variant-card');
    const body = card.querySelector('.vc-body');
    const isOpen = card.classList.contains('is-open');

    if (isOpen) {
        body.style.display = 'none';
        card.classList.remove('is-open');
    } else {
        body.style.display = 'block';
        card.classList.add('is-open');
    }
}

let _allCollapsed = false;
function collapseAllVariants() {
    const cards  = document.querySelectorAll('#variantList .variant-card');
    const btn    = document.getElementById('collapseAllBtn');
    _allCollapsed = !_allCollapsed;

    cards.forEach(function (card) {
        const body = card.querySelector('.vc-body');
        if (_allCollapsed) {
            body.style.display = 'none';
            card.classList.remove('is-open');
        } else {
            body.style.display = 'block';
            card.classList.add('is-open');
        }
    });

    if (btn) btn.textContent = _allCollapsed ? 'Expand All' : 'Collapse All';
}

// ─── Image Preview ────────────────────────────────────────────────────────────
function previewImage(input) {
    const wrap = input.nextElementSibling;
    if (!wrap) return;
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            let img = wrap.querySelector('.img-thumb');
            if (!img) {
                img = document.createElement('img');
                img.className = 'img-thumb';
                img.alt = 'variant image';
                wrap.appendChild(img);
            }
            img.src = e.target.result;
            wrap.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function escHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function escAttr(str) {
    if (!str) return '';
    return String(str).replace(/"/g, '&quot;');
}




  function cartesian(arrays) {
    return arrays.reduce((a, b) => a.flatMap(d => b.map(e => [...d, e])), [[]]);
  }

 function previewVariantImage(input, index) {
  const file = input.files[0];
  const preview = document.getElementById(`variant-img-preview-${index}`);
  if (file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      preview.src = e.target.result;
      preview.style.display = 'block';
    }
    reader.readAsDataURL(file);
  }

  }


  
