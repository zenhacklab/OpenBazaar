/**
* App Module
*
* Main App Module
*/
var app = angular.module('dummyapp', ['ui.router']);

app.config(function($stateProvider, $urlRouterProvider) {
		$stateProvider
			.state('viewStore', {
				url: "",
				views: {
					"main":{
						templateUrl: "layouts/store/storepage.html",
						controller: "storepageCntrl"
					},
					"option":{
						templateUrl: "layouts/store/listcatalog.html",
						controller: "storepageCntrl"
					},
					"sidenav":{
						templateUrl: "layouts/nav.html"
					}
				}
			});

			$urlRouterProvider.otherwise("");

			//	For Later Use
			//	
			//	.state('viewList', {
			//		url: "",
			//		view: {
			//			"main":{
			//				templateUrl: "store/catalogpage.html",
			//				controller: "catalogCntrl"
			//			},
			//			"option":{
			//				templateUrl: "store/listrecent.html",
			//				controller: "userCntrl"
			//			}
			//		},
			//		title:"OpenBazaar",
			//	})
			//	.state('viewUser', {
			//		url: "",
			//		view: {
			//			"main":{
			//				templateUrl: "store/userpage.html",
			//				controller: "userCntrl"
			//			},
			//			"option":{
			//				templateUrl: "store/userchat.html",
			//				controller: "chatclientCntrl"
			//			}
			//		},
			//		title:"OpenBazaar",
			//	})
			//	.state('makeAccount', {
			//		url: "",
			//		view: {
			//			"main":{
			//				templateUrl: "store/accountpage.html",
			//				controller: "storepageCntrl"
			//			},
			//			"option":{
			//				templateUrl: "store/userchat.html",
			//				controller: "keymakerCntrl"
			//			}
			//		},
			//		title:"OpenBazaar",
			//	});

});

// Controllers 

// Index Page Controller
app.controller('indexCntrl', function($scope){});

// Store Page Controller
app.controller('storepageCntrl', function($scope){});


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

			$element.on('mousedown',function(event) {
				event.preventDefault();
				var startX = event.pageX;
				var startY = event.pageY;
				var lwidth = $($attrs.resizerLeft).width();
				var rwidth = $($attrs.resizerRight).width();
				var wwidth = $('#ui-wrap').width();

				$(document).on('mousemove',{
					startX: startX,
					startY: startY,
					lwidth: lwidth,
					rwidth: rwidth,
					wwidth: wwidth
				},mousemove);

				$(document).on('mouseup', mouseup);
			});

			function mousemove(event) {

				if ($attrs.resizerBar == 'vertical') {

					// Redifine Start Orientation
					var startX = event.data.startX;
					var startY = event.data.startY;

					// Redefine Variables from Event Data
					var lwidth = event.data.lwidth;
					var rwidth = event.data.rwidth;
					var wwidth = event.data.wwidth;

					// Handle vertical resizer
					var x = event.pageX - startX;
					var y = event.pageY - startY;

					// Check Max Resizing
					if ($attrs.resizerMax && Math.abs(x) > $attrs.resizerMax) {
						if (x < 0) {x = -parseInt($attrs.resizerMax, 10);}
						else { x = parseInt($attrs.resizerMax, 10);}
					}

					$($attrs.resizerLeft).css({
						width: convrtoperc((lwidth + x),wwidth) + '%'
					});
					$($attrs.resizerRight).css({
						width: convrtoperc((rwidth + -x),wwidth) + '%'
					});

				}
			}

			function mouseup() {
				$(document).unbind('mousemove', mousemove);
				$(document).unbind('mouseup', mouseup);
			}

			function convrtoperc(x,w) {
					var wwidth = w;
					var xperc = 100*(x / w);
					return xperc;
            }
		}
	};
});

