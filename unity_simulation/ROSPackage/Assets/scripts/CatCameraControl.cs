using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CatCameraControl : MonoBehaviour
{
    public Transform target;
    public void SetCameraPosToChooseCar(Transform target)
    {
        this.transform.position = target.position;    
        this.transform.rotation = target.rotation; 
        this.transform.parent = target;
    }

}
