typedef struct _Array{
    int length;
    int a[3];
}Array;
Array g(Array x){
    return x;
}
//void f(int *x,int *y){
//    int t;
//    t=*x;
//    *x=*y;
//    *y=t;
//}
//int sum(Array *a){
//    int s,i;
//    s=0;
//    for(i=0;i<a->length;++i)
//        s+=a->a[i];
//    return s;
//}
//void sort(int a[],int l,int r){
// 	int mid,i,j,k;
// 	mid=a[l+r>>1],i=l,j=r;
// 	do{
// 		while(a[i]<mid) i++;
// 		while(a[j]>mid) j--;
// 		if(i<=j){
// 			int t;
// 			t=a[i];
// 			a[i]=a[j];
// 			a[j]=t;
// 			i++;
// 			j--;
// 		}
// 	}while(i<=j);
// 	if(l<j) sort(a,l,j);
// 	if(i<r) sort(a,i,r);
//}
int main(){
Array x;
g(x).a[2]=4;
//    double x;
//    int a[8];
//    a[0]=1;
//    a[1]=4;
//    a[2]=2;
//    a[3]=8;
//    a[4]=5;
//    a[5]=7;
//    sort(a,0,5);
    return 0;
//    f().a[4]=2;
}
//
//struct A{int x;};
//{
//    struct A{
//    int x,y;
//    };
//}
//struct A{
//    struct B{
//        struct A{
//            int x;
//        }y;
//    }z;
//}