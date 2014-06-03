/**
* App Module
*
* Main App Module
*/
var app = angular.module('dummyapp', ['ui.router','ngAnimate']);

app.config(function($stateProvider, $urlRouterProvider) {

		$stateProvider
			.state('nav', {
				abstract: true,
				templateUrl:"layouts/nav.html"
			})
			.state('nav.catalog', {
				url: "/catalog",
				views: {
					"list":{
						templateUrl: "layouts/list/categories.html",
						controller: "catalogCntrl"
					},
					"view":{
						templateUrl: "layouts/view/blank.html",
						controller: "catalogCntrl"
					}
				}
			})
			.state('nav.catalog-view', {
				url: "/catalog/:category",
				views: {
					"list":{
						templateUrl: "layouts/list/categories.html",
						controller: "catalogCntrl"
					},
					"view":{
						templateUrl: "layouts/view/category.html",
						controller: "catalogCntrl"
					}
				}
			})
			.state('nav.favorites', {
				url: "/favorites",
				views: {
					"list":{
						templateUrl: "layouts/list/favorites.html",
						controller: "favoritesCntrl"
					},
					"view":{
						templateUrl: "layouts/view/blank.html",
						controller: "favoritesCntrl"
					}
				}
			})
			.state('nav.favorites-view', {
				url: "/favorites/:product",
				replace:true,
				views: {
					"list":{
						templateUrl: "layouts/list/favorites.html",
						controller: "favoritesCntrl"
					},
					"view":{
						templateUrl: "layouts/view/favorite.html",
						controller: "favoritesCntrl"
					}
				}
			})
			.state('nav.store', {
				url: "/:page/:ctgry",
				views: {
					"view":{
						templateUrl: "layouts/view/favorites.html",
						controller: "favoritesCntrl"
					},
					"list":{
						templateUrl: "layouts/options/categories.html",
						controller: "favoritesCntrl"
					}
				}
			})
			.state('nav.history', {
				url: "/history",
				views: {
					"list":{
						templateUrl: "layouts/list/history.html",
						controller: "historyCntrl"
					},
					"view":{
						templateUrl: "layouts/view/order.html",
						controller: "historyCntrl"
					}
				}
			})
			.state('nav.cart', {
				url: "/history",
				views: {
					"list":{
						templateUrl: "layouts/list/cart.html",
						controller: "cartCntrl"
					},
					"view":{
						templateUrl: "layouts/view/order.html",
						controller: "cartCntrl"
					}
				}
			});

			$urlRouterProvider.otherwise("/catalog");


});

// Controllers 

// Index Page Controller
app.controller('indexCntrl', function($scope){});

// Store Controller
app.controller('storeCntrl', function($scope){});

// History Purchases Controller
app.controller('historyCntrl', function($scope){});

// Cart - Current Purchases Controller
app.controller('cartCntrl', function($scope){});

// Catalog Controller
app.controller('catalogCntrl', function($scope,$stateParams){

	$scope.categories = [
		{
			title:"Category Title",
			url:"/category1",
			info:"Lorem Ipsum Dolor Est"
		},
		{
			title:"Category Title",
			url:"/category2",
			info:"Lorem Ipsum Dolor Est"
		},
		{
			title:"Category Title",
			url:"/category3",
			info:"Lorem Ipsum Dolor Est"
		}
	];
	$scope.category = $stateParams.category;

});

// Favorites Controller
app.controller('favoritesCntrl', function($scope,$stateParams){

	$scope.favorites = [
		{
			title:"Favorite Item ",
			url:"/item1",
			info:"Lorem Ipsum Dolor Est"
		},
		{
			title:"Favorite Item ",
			url:"/item2",
			info:"Lorem Ipsum Dolor Est"
		},
		{
			title:"Favorite Item ",
			url:"/item3",
			info:"Lorem Ipsum Dolor Est"
		}
	];
	$scope.favorite = $stateParams.product;


});


// Set Wrap Application to 100%
app.directive('uiWrap',function(){
	return {
		restrict: "C",
		link: function($scope,elem,attrs) {
			$(window).resize(function() {

				var height = $(window).height();
				height = height -$('#top-wrap').height();
				$(elem).height(height);

			}).resize();
		}
	};
});

// Resize Bar Directive
app.directive('resizerBar',function($document) {
	return {
		restrict: "A",
		link: function($scope,$element,$attrs) {

			// Check for Parameters
			if(!$attrs.resizerLeft || !$attrs.resizerRight || !$attrs.resizerMax){console.error("Missing Resizer Parameter(s)!");}

			// Check if Change Attribute is Changed or not.
			if ($attrs.change !== 0 && !$attrs.change){$attrs.change = 0;}
			var totalchange = parseInt($attrs.change, 10),
				xmax = parseInt($attrs.resizerMax, 10);

			// Define Percent Change Function (and prevent both resizers from acting the same time)
			function convrtoperc(x,w) {
					return 100*(x / w);
            }

			$element.on('mousedown',function(event) {
				event.preventDefault();

				// Find Current Widths on Click
				var lwidth = $($attrs.resizerLeft).width(),
					rwidth = $($attrs.resizerRight).width(),
					startX = event.pageX,
					startY = event.pageY,
					wwidth = $('#ui-wrap').width();

				$document
					.on('mousemove',function(event) {
						if ($attrs.resizerBar == 'vertical') {

							// Handle vertical resizer
							var x = event.pageX - startX,
								y = event.pageY - startY;

							// Find Current Position
							totalchange = parseInt($attrs.change, 10) + x;

							if(Math.abs(totalchange) <= xmax){
								$($attrs.resizerLeft).css({
									width: convrtoperc((lwidth + x),wwidth) + '%'
								});
								$($attrs.resizerRight).css({
									width: convrtoperc((rwidth + -x),wwidth) + '%'
								});
							} else {

								// Optional "Bouncy" Sliders
								// var overmove = Math.abs(Math.abs(totalchange) - xmax),
								//	overbounce = 50;

								if(x < 0){
									// if(overmove < overbounce) {
									//	$('#ui-wrap').css({ "left" : -overmove + "px"});
									// }
									totalchange = -xmax;
								}
								if(x > 0){
									// if(overmove < overbounce) {
									//	$('#ui-wrap').css({ "left" : overmove + "px"});
									// }
									totalchange = xmax;
								}
							}
						}
					})
					.on('mouseup', function() {
						// $('#ui-wrap').css({ "left" : ""});
						$attrs.$set("change",totalchange);
						$document.unbind('mousemove');
						$document.unbind('mouseup');
					});
			});
			
		}
	};
});

