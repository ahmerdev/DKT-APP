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

        // Clear input so same file can be selected again
        e.target.value = '';
    });



// VARIATIONS PART

document.getElementById('productTypeToggleSwitch').addEventListener('change', function () {
  const isChecked = this.checked;
  const type = isChecked ? 'variable' : 'simple';
  document.getElementById("productTypeInput").value = type;

  const variantSection = document.getElementById('variantSection');
  if (type === 'variable') {
    variantSection.style.display = 'block';
    document.querySelectorAll('[name=SKU], [name=quantity], [name=regular_price], [name=sale_price]').forEach(el => {
      el.closest('fieldset').style.display = 'none';
    });
  } else {
    variantSection.style.display = 'none';
    document.querySelectorAll('[name=SKU], [name=quantity], [name=regular_price], [name=sale_price]').forEach(el => {
      el.closest('fieldset').style.display = 'block';
    });
  }
});

let optionCount = 0;

function addOption() {
  optionCount++;
  const container = document.createElement('div');
  container.classList.add('mb-3');
  container.innerHTML = `
    <div class="row align-items-end option-row">
      <div class="col-md-5">
        <label class="form-label">Option ${optionCount} Name</label>
        <input type="text" class="form-control option-name" placeholder="e.g. Size or Color">
      </div>
      <div class="col-md-5">
        <label class="form-label">Values</label>
        <input type="text" class="form-control option-values" placeholder="Comma separated values (e.g. S,M,L)">
      </div>
      <div class="col-md-2">
        <button type="button" class="tf-button mt-2 remove-option">
          <i class="fa-solid fa-trash-can shadow"></i>
        </button>
      </div>
    </div>
  `;

  document.getElementById('optionContainer').appendChild(container);

  // naye input fields par listener lagao
  container.querySelectorAll("input").forEach(el => {
    el.addEventListener("input", generateVariants);
  });

  // remove button listener
  container.querySelector(".remove-option").addEventListener("click", function () {
    container.remove();
    generateVariants(); // delete ke baad regenerate
  });
}

function generateVariants() {
  const names = Array.from(document.querySelectorAll('.option-name'))
    .map(el => el.value.trim())
    .filter(Boolean);

  const values = Array.from(document.querySelectorAll('.option-values'))
    .map(el => el.value.split(',').map(v => v.trim()).filter(Boolean));

  if (!names.length || !values.length || names.length !== values.length) return;

  const combos = cartesian(values); // [["Red","S"],["Red","M"],...]

  const variantList = document.getElementById('variantList');

  // 🟢 STEP 1: Purane data store karo
  let oldData = {};
  variantList.querySelectorAll(".card").forEach(card => {
    const label = card.querySelector("h6").innerText.trim();
    oldData[label] = {
      sku: card.querySelector("input[name*='[sku]']")?.value,
      stock: card.querySelector("input[name*='[stock]']")?.value,
      regular_price: card.querySelector("input[name*='[regular_price]']")?.value,
      sale_price: card.querySelector("input[name*='[sale_price]']")?.value,
      points: card.querySelector("input[name*='[points]']")?.value,
      description: card.querySelector("textarea[name*='[description]']")?.value,
      image_url: card.querySelector("img")?.getAttribute("src") || ""
    };
  });

  // 🟢 STEP 2: Purani list clear karke nayi banani
  variantList.innerHTML = '';

  combos.forEach((combo, index) => {
    const label = combo.join(' / ');
    const optionsObj = {};
    names.forEach((n, i) => optionsObj[n] = combo[i]);
    const optionsJSON = JSON.stringify(optionsObj).replace(/"/g, '&quot;');

    const prev = oldData[label] || {};

    variantList.insertAdjacentHTML('beforeend', `
      <div class="col-md-12">
        <div class="card shadow-sm border-0 rounded-4 mb-4">
          <div class="card-body">
            <h6 class="fw-bold mb-3 text-danger">${label}</h6>
            <input type="hidden" name="variants[${index}][options]" value="${optionsJSON}">
            <div class="row g-3">
              <!-- SKU -->
              <div class="col-md-6">
                <fieldset class="name">
                  <div class="body-title mb-10">SKU</div>
                  <input class="mb-10" type="text" name="variants[${index}][sku]" placeholder="Enter SKU" value="${prev.sku || ''}">
                </fieldset>
              </div>
              <!-- Stock -->
              <div class="col-md-6">
                <fieldset class="name">
                  <div class="body-title mb-10">Quantity</div>
                  <input class="mb-10" type="number" name="variants[${index}][stock]" placeholder="Enter quantity" value="${prev.stock || ''}">
                </fieldset>
              </div>
              <!-- Prices -->
              <div class="col-md-6">
                <fieldset class="name">
                  <div class="body-title mb-10">Regular Price *</div>
                  <input class="mb-10" type="text" name="variants[${index}][regular_price]" required placeholder="Enter regular price" value="${prev.regular_price || ''}">
                </fieldset>
              </div>
              <div class="col-md-6">
                <fieldset class="name">
                  <div class="body-title mb-10">Sale Price</div>
                  <input class="mb-10" type="text" name="variants[${index}][sale_price]" placeholder="Enter sale price" value="${prev.sale_price || ''}">
                </fieldset>
              </div>
              <!-- Points -->
              <div class="col-md-12">
                <fieldset class="name">
                  <div class="body-title mb-10">Points</div>
                  <input class="mb-10" type="number" name="variants[${index}][points]" value="${prev.points || ''}">
                </fieldset>
              </div>
              <!-- Description -->
              <div class="col-md-12">
                <fieldset class="description">
                  <div class="body-title mb-10">Description</div>
                  <textarea class="mb-10" name="variants[${index}][description]" placeholder="Description">${prev.description || ''}</textarea>
                </fieldset>
              </div>
              <!-- Image -->
              <div class="col-md-12">
                <fieldset>
                  <div class="body-title">Upload images <span class="tf-color-1">*</span></div>
                  <input type="file" accept="image/*" name="variants[${index}][image]" class="form-control">
                  ${prev.image_url 
                    ? `<div class="mt-2">
                         <img src="${prev.image_url}" alt="Preview" style="max-height:100px;border-radius:6px;">
                         <input type="hidden" name="variants[${index}][old_image]" value="${prev.image_url}">
                       </div>` 
                    : ""}
                </fieldset>
              </div>
            </div>
          </div>
        </div>
      </div>
    `);
  });
}

// Cartesian product helper
function cartesian(arr) {
  return arr.reduce((a, b) => a.flatMap(d => b.map(e => [...d, e])), [[]]);
}

// --------------------
// INIT ON PAGE LOAD
// --------------------
document.addEventListener("DOMContentLoaded", function () {
  const productType = document.getElementById("productTypeInput")?.value;
  if (productType === "variable") {
    // existing option fields listeners
    document.querySelectorAll('.option-name, .option-values').forEach(el => {
      el.addEventListener("input", generateVariants);
    });

    // page load par variants regenerate
    generateVariants();
  }
});





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


  