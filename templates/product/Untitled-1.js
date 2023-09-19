 $(document).on("change", ".quantity-input", function(event) {
                  event.preventDefault();
                  console.log("Quantity input changed");
                  var product_id = $(this).data("product-id");
                  var new_quantity = $(this).val();
          
                  $.ajax({
                      type: "POST",
                      url: '/update-cart-quantity',
                      data: {
                          csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
                          product_id: product_id,
                          new_quantity: new_quantity
                      },
                      dataType: "json",
                      success: function(data) {
                          if (data.message) {
                              // Update the cart total or any other UI elements as needed
                              console.log(data.message);
                          }
                      },
                      error: function(xhr, textStatus, errorThrown) {
                          console.error("Error: " + errorThrown);
                      }
                  });
              });
              