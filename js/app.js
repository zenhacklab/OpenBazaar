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
				height = height - 15 -$('#top-wrap').height();
				$(elem).height(height);

			}).resize();
		}
	};
});


// app.directive('resizerBar',function($document) {
// 	return {
// 		restrict: "A",
// 		link: function($scope,$element,$attrs) {
// 			$element.on('mousedown',function(event) {
// 				event.preventDefault();
// 				var startX = event.pageX;
// 				var startY = event.pageY;

// 				$(document).on('mousemove',{startX: startX, startY:startY},mousemove);
// 				$(document).on('mouseup', mouseup);
// 			});

// 			function mousemove(event) {

//             if ($attrs.resizerBar == 'vertical') {

// 				// Redifine Start Orientation
// 				var startX = event.data.startX;
// 				var startY = event.data.startY;

//                 // Handle vertical resizer
//                 var x = startX - event.pageX;
//                 var y = startY - event.pageY;

//                 if ($attrs.resizerMax && Math.abs(x) > $attrs.resizerMax) {
//                     x = parseInt($attrs.resizerMax, 10);
//                 }

//                 var currentwidth = $(window).resize(function() {
// 					return $($attrs.resizerLeft).width();
// 				}).resize();

//                 $element.css({
//                     right: x + 'px'
//                 });

//                 $($attrs.resizerLeft).css({
//                     width: currentwidth + x + 'px'
//                 });
//                 $($attrs.resizerRight).css({
//                     left: (x + parseInt($attrs.resizerWidth, 10)) + 'px'
//                 });

//             }
//         }

//         function mouseup() {
//             $(document).unbind('mousemove', mousemove);
//             $(document).unbind('mouseup', mouseup);
//         }

// 		}
// 	};
// });

