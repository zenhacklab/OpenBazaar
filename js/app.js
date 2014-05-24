/**
* App Module
*
* Main App Module
*/
var app = angular.module('dummyapp', ['ui.router']);

app.config(['$stateProvider','$urlRouterProvider',
	function($stateProvider, $urlRouterProvider) {
		$urlRouterProvider.otherwise("");

		$stateProvider
			.state('viewStore', {
				url: "",
				view: {
					"main":{
						templateUrl: "store/storepage.html",
						controller: "storepageCntrl"
					},
					"option":{
						templateUrl: "store/listcatalog.html",
						controller: "storelistCntrl"
					}
				},
				title:"OpenBazaar",
			});

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

}]);

// Controllers 

// Index Page Controller
app.controller('indexCntrl', function($scope){});

// Store Page Controller
app.controller('storepageCntrl', function($scope){});

// Store List Controller
app.controller('storelistCntrl', function($scope){});


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

